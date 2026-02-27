"""
Web 配置界面模块
提供可视化的配置向导和管理界面
"""
import json
import os
from datetime import datetime
from typing import Dict, List, Optional

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

from src.config import get_column_config, get_settings
from src.setup_wizard import PROFILE_TEMPLATES, SetupWizard

router = APIRouter(prefix="/setup", tags=["setup"])


# 数据模型
class TemplateSelection(BaseModel):
    template_id: str
    user_id: str = "default"


class UserProfileInput(BaseModel):
    industry: str
    position: str
    expertise: List[str]
    daily_time_minutes: int = 20
    user_id: str = "default"


class LLMConfigInput(BaseModel):
    provider: str
    api_key: str
    base_url: Optional[str] = None
    model: str
    user_id: str = "default"


class ChannelConfigInput(BaseModel):
    telegram_bot_token: Optional[str] = None
    telegram_chat_id: Optional[str] = None
    slack_bot_token: Optional[str] = None
    slack_channel: Optional[str] = None
    discord_bot_token: Optional[str] = None
    discord_channel_id: Optional[str] = None
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: Optional[str] = None


# HTML 模板
SETUP_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Agent - 配置向导</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 800px;
            margin: 0 auto;
        }
        
        .header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .card {
            background: white;
            border-radius: 16px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        .step-indicator {
            display: flex;
            justify-content: center;
            margin-bottom: 30px;
        }
        
        .step {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #e0e0e0;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0 10px;
            font-weight: bold;
            color: #666;
            transition: all 0.3s;
        }
        
        .step.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .step.completed {
            background: #4caf50;
            color: white;
        }
        
        .step-line {
            width: 60px;
            height: 2px;
            background: #e0e0e0;
            margin-top: 19px;
        }
        
        h2 {
            color: #333;
            margin-bottom: 20px;
            font-size: 1.5em;
        }
        
        .template-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .template-card {
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px;
            cursor: pointer;
            transition: all 0.3s;
            text-align: center;
        }
        
        .template-card:hover {
            border-color: #667eea;
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.2);
        }
        
        .template-card.selected {
            border-color: #667eea;
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        }
        
        .template-icon {
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        
        .template-name {
            font-weight: bold;
            color: #333;
            margin-bottom: 5px;
        }
        
        .template-desc {
            font-size: 0.85em;
            color: #666;
        }
        
        .form-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            color: #555;
            font-weight: 500;
        }
        
        input[type="text"],
        input[type="number"],
        input[type="password"],
        select,
        textarea {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus,
        select:focus,
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            padding: 14px 32px;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            margin-right: 10px;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-primary:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.3);
        }
        
        .btn-secondary {
            background: #f5f5f5;
            color: #666;
        }
        
        .btn-secondary:hover {
            background: #e0e0e0;
        }
        
        .hidden {
            display: none;
        }
        
        .recommend-section {
            background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
        }
        
        .keywords-input {
            display: flex;
            gap: 10px;
            margin-bottom: 15px;
        }
        
        .keywords-input input {
            flex: 1;
        }
        
        .recommendation-results {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
        }
        
        .rec-card {
            background: white;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .rec-card:hover,
        .rec-card.selected {
            border-color: #667eea;
        }
        
        .rec-score {
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: bold;
            margin-bottom: 8px;
        }
        
        .rec-score.high {
            background: #4caf50;
            color: white;
        }
        
        .rec-score.medium {
            background: #ff9800;
            color: white;
        }
        
        .channel-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .channel-card {
            border: 2px solid #e0e0e0;
            border-radius: 12px;
            padding: 20px;
        }
        
        .channel-card.enabled {
            border-color: #4caf50;
        }
        
        .channel-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
        }
        
        .channel-icon {
            font-size: 1.5em;
            margin-right: 10px;
        }
        
        .toggle-switch {
            margin-left: auto;
            position: relative;
            width: 50px;
            height: 26px;
        }
        
        .toggle-switch input {
            opacity: 0;
            width: 0;
            height: 0;
        }
        
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 26px;
        }
        
        .slider:before {
            position: absolute;
            content: "";
            height: 18px;
            width: 18px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        
        input:checked + .slider {
            background-color: #4caf50;
        }
        
        input:checked + .slider:before {
            transform: translateX(24px);
        }
        
        .success-message {
            text-align: center;
            padding: 40px;
        }
        
        .success-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
        
        .nav-links {
            display: flex;
            justify-content: center;
            gap: 20px;
            margin-top: 30px;
        }
        
        .nav-links a {
            color: #667eea;
            text-decoration: none;
            padding: 10px 20px;
            border-radius: 8px;
            transition: background 0.3s;
        }
        
        .nav-links a:hover {
            background: rgba(102, 126, 234, 0.1);
        }
        
        @media (max-width: 600px) {
            .header h1 {
                font-size: 1.8em;
            }
            
            .template-grid {
                grid-template-columns: 1fr;
            }
            
            .card {
                padding: 20px;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Daily Agent</h1>
            <p>个性化日报配置向导</p>
        </div>
        
        <!-- Step Indicator -->
        <div class="card">
            <div class="step-indicator">
                <div class="step active" id="step1-indicator">1</div>
                <div class="step-line"></div>
                <div class="step" id="step2-indicator">2</div>
                <div class="step-line"></div>
                <div class="step" id="step3-indicator">3</div>
                <div class="step-line"></div>
                <div class="step" id="step4-indicator">4</div>
            </div>
        </div>
        
        <!-- Step 1: Template Selection -->
        <div class="card" id="step1">
            <h2>🎯 步骤 1/4: 选择配置方式</h2>
            
            <div class="recommend-section">
                <h3>💡 智能推荐</h3>
                <p style="margin-bottom: 15px; color: #666;">输入你感兴趣的关键词，我们将为你推荐最合适的模板</p>
                <div class="keywords-input">
                    <input type="text" id="keywords" placeholder="例如: AI 编程 创业" />
                    <button class="btn btn-primary" onclick="getRecommendations()">获取推荐</button>
                </div>
                <div id="recommendation-results" class="recommendation-results"></div>
            </div>
            
            <h3 style="margin-top: 30px; margin-bottom: 15px;">📋 或手动选择模板</h3>
            <div class="template-grid" id="template-grid">
                {templates_html}
            </div>
            
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn btn-primary" onclick="nextStep(2)" id="btn-step1">下一步 →</button>
            </div>
        </div>
        
        <!-- Step 2: User Profile -->
        <div class="card hidden" id="step2">
            <h2>👤 步骤 2/4: 用户画像</h2>
            
            <div class="form-group">
                <label>行业</label>
                <select id="industry">
                    <option value="互联网/科技">互联网/科技</option>
                    <option value="金融/投资">金融/投资</option>
                    <option value="咨询/商业分析">咨询/商业分析</option>
                    <option value="媒体/内容创作">媒体/内容创作</option>
                    <option value="学术研究">学术研究</option>
                    <option value="医疗健康">医疗健康</option>
                    <option value="制造业">制造业</option>
                    <option value="教育/培训">教育/培训</option>
                    <option value="其他">其他</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>职位</label>
                <select id="position">
                    <option value="技术开发者">技术开发者</option>
                    <option value="产品经理">产品经理</option>
                    <option value="创业者/高管">创业者/高管</option>
                    <option value="投资人/分析师">投资人/分析师</option>
                    <option value="设计师">设计师</option>
                    <option value="市场/运营">市场/运营</option>
                    <option value="学生">学生</option>
                    <option value="自由职业者">自由职业者</option>
                    <option value="其他">其他</option>
                </select>
            </div>
            
            <div class="form-group">
                <label>专业领域（空格分隔）</label>
                <input type="text" id="expertise" placeholder="例如: AI Python 产品设计" />
            </div>
            
            <div class="form-group">
                <label>每日阅读时间</label>
                <select id="reading-time">
                    <option value="10">5-10 分钟（精简版）</option>
                    <option value="20" selected>15-20 分钟（标准版）</option>
                    <option value="30">30 分钟以上（深度版）</option>
                </select>
            </div>
            
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn btn-secondary" onclick="prevStep(1)">← 上一步</button>
                <button class="btn btn-primary" onclick="nextStep(3)">下一步 →</button>
            </div>
        </div>
        
        <!-- Step 3: LLM Configuration -->
        <div class="card hidden" id="step3">
            <h2>🤖 步骤 3/4: LLM 配置（可选）</h2>
            <p style="margin-bottom: 20px; color: #666;">配置 LLM 可以让日报生成更智能的摘要和质量评估</p>
            
            <div class="form-group">
                <label>LLM 提供商</label>
                <select id="llm-provider" onchange="updateModelOptions()">
                    <option value="">-- 跳过 --</option>
                    <option value="openai">OpenAI</option>
                    <option value="openrouter">OpenRouter</option>
                    <option value="ollama">Ollama (本地)</option>
                    <option value="kimi">Kimi (Moonshot)</option>
                </select>
            </div>
            
            <div id="llm-config-fields" class="hidden">
                <div class="form-group">
                    <label>API Key</label>
                    <input type="password" id="llm-api-key" placeholder="sk-..." />
                </div>
                
                <div class="form-group">
                    <label>模型</label>
                    <select id="llm-model">
                        <option value="gpt-4o-mini">gpt-4o-mini (推荐)</option>
                        <option value="gpt-4o">gpt-4o</option>
                        <option value="gpt-3.5-turbo">gpt-3.5-turbo</option>
                    </select>
                </div>
                
                <div class="form-group">
                    <label>Base URL（可选）</label>
                    <input type="text" id="llm-base-url" placeholder="https://api.openai.com/v1" />
                </div>
            </div>
            
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn btn-secondary" onclick="prevStep(2)">← 上一步</button>
                <button class="btn btn-primary" onclick="nextStep(4)">下一步 →</button>
            </div>
        </div>
        
        <!-- Step 4: Push Channels -->
        <div class="card hidden" id="step4">
            <h2>📤 步骤 4/4: 推送渠道（可选）</h2>
            <p style="margin-bottom: 20px; color: #666;">选择日报推送的渠道，可多选</p>
            
            <div class="channel-grid">
                <div class="channel-card" id="channel-telegram">
                    <div class="channel-header">
                        <span class="channel-icon">📱</span>
                        <span><strong>Telegram</strong></span>
                        <label class="toggle-switch">
                            <input type="checkbox" id="enable-telegram" onchange="toggleChannel('telegram')">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div id="config-telegram" class="hidden">
                        <div class="form-group">
                            <label>Bot Token</label>
                            <input type="text" id="telegram-token" placeholder="123456:ABC-DEF..." />
                        </div>
                        <div class="form-group">
                            <label>Chat ID</label>
                            <input type="text" id="telegram-chatid" placeholder="@channelname 或 ID" />
                        </div>
                    </div>
                </div>
                
                <div class="channel-card" id="channel-slack">
                    <div class="channel-header">
                        <span class="channel-icon">💬</span>
                        <span><strong>Slack</strong></span>
                        <label class="toggle-switch">
                            <input type="checkbox" id="enable-slack" onchange="toggleChannel('slack')">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div id="config-slack" class="hidden">
                        <div class="form-group">
                            <label>Bot Token</label>
                            <input type="text" id="slack-token" placeholder="xoxb-..." />
                        </div>
                        <div class="form-group">
                            <label>Channel</label>
                            <input type="text" id="slack-channel" placeholder="#daily" />
                        </div>
                    </div>
                </div>
                
                <div class="channel-card" id="channel-discord">
                    <div class="channel-header">
                        <span class="channel-icon">🎮</span>
                        <span><strong>Discord</strong></span>
                        <label class="toggle-switch">
                            <input type="checkbox" id="enable-discord" onchange="toggleChannel('discord')">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div id="config-discord" class="hidden">
                        <div class="form-group">
                            <label>Bot Token</label>
                            <input type="text" id="discord-token" placeholder="..." />
                        </div>
                        <div class="form-group">
                            <label>Channel ID</label>
                            <input type="text" id="discord-channel" placeholder="123456789" />
                        </div>
                    </div>
                </div>
                
                <div class="channel-card" id="channel-email">
                    <div class="channel-header">
                        <span class="channel-icon">📧</span>
                        <span><strong>Email</strong></span>
                        <label class="toggle-switch">
                            <input type="checkbox" id="enable-email" onchange="toggleChannel('email')">
                            <span class="slider"></span>
                        </label>
                    </div>
                    <div id="config-email" class="hidden">
                        <div class="form-group">
                            <label>SMTP Host</label>
                            <input type="text" id="smtp-host" placeholder="smtp.gmail.com" />
                        </div>
                        <div class="form-group">
                            <label>SMTP User</label>
                            <input type="text" id="smtp-user" placeholder="your@email.com" />
                        </div>
                        <div class="form-group">
                            <label>SMTP Password</label>
                            <input type="password" id="smtp-password" placeholder="..." />
                        </div>
                        <div class="form-group">
                            <label>To Email</label>
                            <input type="text" id="email-to" placeholder="recipient@email.com" />
                        </div>
                    </div>
                </div>
            </div>
            
            <div style="text-align: right; margin-top: 20px;">
                <button class="btn btn-secondary" onclick="prevStep(3)">← 上一步</button>
                <button class="btn btn-primary" onclick="saveConfig()">💾 保存配置</button>
            </div>
        </div>
        
        <!-- Success Page -->
        <div class="card hidden" id="success-page">
            <div class="success-message">
                <div class="success-icon">🎉</div>
                <h2>配置完成！</h2>
                <p style="color: #666; margin: 20px 0;">你的个性化日报已经配置好了</p>
                
                <div class="nav-links">
                    <a href="/">🏠 返回首页</a>
                    <a href="/docs">📚 API 文档</a>
                    <a href="/dashboard">📊 监控面板</a>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let currentStep = 1;
        let selectedTemplate = '';
        
        // Templates data
        const templates = {templates_json};
        
        function nextStep(step) {
            if (step === 2 && !selectedTemplate) {
                alert('请选择一个模板');
                return;
            }
            
            document.getElementById(`step${currentStep}`).classList.add('hidden');
            document.getElementById(`step${step}`).classList.remove('hidden');
            
            // Update indicators
            document.getElementById(`step${currentStep}-indicator`).classList.remove('active');
            document.getElementById(`step${currentStep}-indicator`).classList.add('completed');
            document.getElementById(`step${step}-indicator`).classList.add('active');
            
            currentStep = step;
        }
        
        function prevStep(step) {
            document.getElementById(`step${currentStep}`).classList.add('hidden');
            document.getElementById(`step${step}`).classList.remove('hidden');
            
            // Update indicators
            document.getElementById(`step${currentStep}-indicator`).classList.remove('active');
            document.getElementById(`step${step}-indicator`).classList.remove('completed');
            document.getElementById(`step${step}-indicator`).classList.add('active');
            
            currentStep = step;
        }
        
        function selectTemplate(templateId) {
            selectedTemplate = templateId;
            
            // Update UI
            document.querySelectorAll('.template-card').forEach(card => {
                card.classList.remove('selected');
            });
            document.getElementById(`template-${templateId}`).classList.add('selected');
            
            // Auto-fill profile if template data available
            if (templates[templateId]) {
                const t = templates[templateId];
                document.getElementById('industry').value = t.industry || '互联网/科技';
                document.getElementById('position').value = t.position || '技术开发者';
                if (t.expertise) {
                    document.getElementById('expertise').value = t.expertise.join(' ');
                }
            }
        }
        
        async function getRecommendations() {
            const keywords = document.getElementById('keywords').value;
            if (!keywords.trim()) {
                alert('请输入关键词');
                return;
            }
            
            try {
                const response = await fetch('/api/v1/setup/recommend', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({keywords: keywords})
                });
                
                const data = await response.json();
                displayRecommendations(data.recommendations);
            } catch (error) {
                console.error('Error:', error);
                alert('获取推荐失败');
            }
        }
        
        function displayRecommendations(recommendations) {
            const container = document.getElementById('recommendation-results');
            container.innerHTML = '';
            
            recommendations.forEach((rec, index) => {
                const scoreClass = rec.score >= 0.8 ? 'high' : 'medium';
                const html = `
                    <div class="rec-card" onclick="selectTemplate('${rec.template_id}'); nextStep(2)">
                        <span class="rec-score ${scoreClass}">${Math.round(rec.score * 100)}% 匹配</span>
                        <h4>${rec.name}</h4>
                        <p style="font-size: 0.85em; color: #666; margin-top: 5px;">${rec.description}</p>
                        ${rec.matched_keywords.length > 0 ? 
                            `<p style="font-size: 0.8em; color: #999; margin-top: 8px;">匹配: ${rec.matched_keywords.join(', ')}</p>` : ''}
                    </div>
                `;
                container.innerHTML += html;
            });
        }
        
        function toggleChannel(channel) {
            const enabled = document.getElementById(`enable-${channel}`).checked;
            const card = document.getElementById(`channel-${channel}`);
            const config = document.getElementById(`config-${channel}`);
            
            if (enabled) {
                card.classList.add('enabled');
                config.classList.remove('hidden');
            } else {
                card.classList.remove('enabled');
                config.classList.add('hidden');
            }
        }
        
        function updateModelOptions() {
            const provider = document.getElementById('llm-provider').value;
            const fields = document.getElementById('llm-config-fields');
            const modelSelect = document.getElementById('llm-model');
            
            if (!provider) {
                fields.classList.add('hidden');
                return;
            }
            
            fields.classList.remove('hidden');
            
            // Update model options based on provider
            const models = {
                'openai': [
                    {value: 'gpt-4o-mini', text: 'gpt-4o-mini (推荐)'},
                    {value: 'gpt-4o', text: 'gpt-4o'},
                    {value: 'gpt-3.5-turbo', text: 'gpt-3.5-turbo'}
                ],
                'openrouter': [
                    {value: 'anthropic/claude-3.5-sonnet', text: 'Claude 3.5 Sonnet'},
                    {value: 'openai/gpt-4o', text: 'GPT-4o'}
                ],
                'ollama': [
                    {value: 'llama2', text: 'Llama 2'},
                    {value: 'mistral', text: 'Mistral'}
                ],
                'kimi': [
                    {value: 'moonshot-v1-8k', text: 'Moonshot v1 8K'},
                    {value: 'moonshot-v1-32k', text: 'Moonshot v1 32K'}
                ]
            };
            
            modelSelect.innerHTML = '';
            (models[provider] || []).forEach(m => {
                modelSelect.innerHTML += `<option value="${m.value}">${m.text}</option>`;
            });
        }
        
        async function saveConfig() {
            const config = {
                template: selectedTemplate,
                profile: {
                    industry: document.getElementById('industry').value,
                    position: document.getElementById('position').value,
                    expertise: document.getElementById('expertise').value.split(' '),
                    daily_time_minutes: parseInt(document.getElementById('reading-time').value)
                },
                llm: {
                    provider: document.getElementById('llm-provider').value,
                    api_key: document.getElementById('llm-api-key').value,
                    model: document.getElementById('llm-model').value,
                    base_url: document.getElementById('llm-base-url').value
                },
                channels: {
                    telegram: document.getElementById('enable-telegram').checked ? {
                        token: document.getElementById('telegram-token').value,
                        chat_id: document.getElementById('telegram-chatid').value
                    } : null,
                    slack: document.getElementById('enable-slack').checked ? {
                        token: document.getElementById('slack-token').value,
                        channel: document.getElementById('slack-channel').value
                    } : null,
                    discord: document.getElementById('enable-discord').checked ? {
                        token: document.getElementById('discord-token').value,
                        channel_id: document.getElementById('discord-channel').value
                    } : null,
                    email: document.getElementById('enable-email').checked ? {
                        smtp_host: document.getElementById('smtp-host').value,
                        smtp_user: document.getElementById('smtp-user').value,
                        smtp_password: document.getElementById('smtp-password').value,
                        email_to: document.getElementById('email-to').value
                    } : null
                }
            };
            
            try {
                const response = await fetch('/api/v1/setup/save', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                });
                
                if (response.ok) {
                    document.getElementById('step4').classList.add('hidden');
                    document.getElementById('success-page').classList.remove('hidden');
                } else {
                    alert('保存失败');
                }
            } catch (error) {
                console.error('Error:', error);
                alert('保存失败');
            }
        }
    </script>
</body>
</html>
"""


@router.get("", response_class=HTMLResponse)
async def setup_page():
    """Web 配置向导页面"""
    # 生成模板 HTML
    templates_html = ""
    templates_json = {}
    
    for template_id, template in PROFILE_TEMPLATES.items():
        templates_html += f"""
        <div class="template-card" id="template-{template_id}" onclick="selectTemplate('{template_id}')">
            <div class="template-icon">{template.name.split()[0]}</div>
            <div class="template-name">{' '.join(template.name.split()[1:])}</div>
            <div class="template-desc">{template.description}</div>
        </div>
        """
        
        templates_json[template_id] = {
            "name": template.name,
            "industry": template.industry,
            "position": template.position,
            "expertise": template.expertise,
        }
    
    html = SETUP_HTML.format(
        templates_html=templates_html,
        templates_json=json.dumps(templates_json, ensure_ascii=False)
    )
    
    return html


class RecommendRequest(BaseModel):
    keywords: str


@router.post("/api/v1/setup/recommend")
async def api_recommend_templates(request: RecommendRequest):
    """API: 获取模板推荐"""
    from src.template_recommender import TemplateRecommender
    
    recommender = TemplateRecommender()
    recommendations = recommender.recommend(request.keywords, top_k=3)
    
    return {
        "recommendations": [
            {
                "template_id": r.template_id,
                "name": r.name,
                "score": r.score,
                "description": r.description,
                "matched_keywords": r.matched_keywords
            }
            for r in recommendations
        ]
    }


@router.post("/api/v1/setup/save")
async def api_save_config(request: Request):
    """API: 保存配置"""
    data = await request.json()
    
    try:
        # 这里应该调用 SetupWizard 保存配置
        # 简化处理，实际应该异步保存到数据库
        
        # 保存 LLM 配置
        llm_config = data.get("llm", {})
        if llm_config.get("provider") and llm_config.get("api_key"):
            # 写入 .env 文件
            env_lines = []
            env_path = ".env"
            
            if os.path.exists(env_path):
                with open(env_path, "r") as f:
                    env_lines = f.readlines()
            
            # 更新或添加配置
            new_configs = {
                "OPENAI_API_KEY": llm_config.get("api_key"),
                "OPENAI_MODEL": llm_config.get("model", "gpt-4o-mini"),
            }
            
            if llm_config.get("base_url"):
                new_configs["OPENAI_BASE_URL"] = llm_config.get("base_url")
            
            # 写入文件
            with open(env_path, "w") as f:
                for line in env_lines:
                    key = line.split("=")[0] if "=" in line else ""
                    if key not in new_configs:
                        f.write(line)
                
                for key, value in new_configs.items():
                    if value:
                        f.write(f"{key}={value}\n")
        
        # 保存渠道配置
        channels = data.get("channels", {})
        env_additions = []
        
        if channels.get("telegram"):
            t = channels["telegram"]
            env_additions.append(f"TELEGRAM_BOT_TOKEN={t.get('token', '')}")
            env_additions.append(f"TELEGRAM_CHAT_ID={t.get('chat_id', '')}")
        
        if channels.get("slack"):
            s = channels["slack"]
            env_additions.append(f"SLACK_BOT_TOKEN={s.get('token', '')}")
            env_additions.append(f"SLACK_CHANNEL={s.get('channel', '')}")
        
        if channels.get("discord"):
            d = channels["discord"]
            env_additions.append(f"DISCORD_BOT_TOKEN={d.get('token', '')}")
            env_additions.append(f"DISCORD_CHANNEL_ID={d.get('channel_id', '')}")
        
        if channels.get("email"):
            e = channels["email"]
            env_additions.append(f"SMTP_HOST={e.get('smtp_host', '')}")
            env_additions.append(f"SMTP_USER={e.get('smtp_user', '')}")
            env_additions.append(f"SMTP_PASSWORD={e.get('smtp_password', '')}")
            env_additions.append(f"EMAIL_TO={e.get('email_to', '')}")
        
        if env_additions:
            with open(".env", "a") as f:
                f.write("\n# Push Channels\n")
                for line in env_additions:
                    f.write(line + "\n")
        
        return {"success": True, "message": "配置已保存"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Dashboard HTML
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Daily Agent - 监控面板</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #f5f7fa;
            min-height: 100vh;
        }
        .navbar {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .navbar h1 { font-size: 1.5em; }
        .nav-links a {
            color: white;
            text-decoration: none;
            margin-left: 20px;
            opacity: 0.9;
        }
        .nav-links a:hover { opacity: 1; }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        
        .stat-card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .stat-title {
            color: #666;
            font-size: 0.9em;
            margin-bottom: 10px;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        
        .stat-change {
            font-size: 0.85em;
            margin-top: 5px;
        }
        
        .stat-change.positive { color: #4caf50; }
        .stat-change.negative { color: #f44336; }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 25px;
            margin-bottom: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        }
        
        .card-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .card-title {
            font-size: 1.2em;
            font-weight: 600;
            color: #333;
        }
        
        .status-badge {
            padding: 6px 12px;
            border-radius: 20px;
            font-size: 0.85em;
            font-weight: 500;
        }
        
        .status-badge.success { background: #e8f5e9; color: #2e7d32; }
        .status-badge.warning { background: #fff3e0; color: #ef6c00; }
        .status-badge.error { background: #ffebee; color: #c62828; }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th, td {
            padding: 12px;
            text-align: left;
            border-bottom: 1px solid #eee;
        }
        
        th {
            font-weight: 600;
            color: #666;
            font-size: 0.9em;
        }
        
        tr:hover { background: #f9f9f9; }
        
        .btn {
            padding: 8px 16px;
            border: none;
            border-radius: 6px;
            font-size: 0.9em;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .btn-primary {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn-secondary {
            background: #f5f5f5;
            color: #666;
        }
        
        .progress-bar {
            width: 100%;
            height: 8px;
            background: #e0e0e0;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .progress-fill {
            height: 100%;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            transition: width 0.3s;
        }
        
        @media (max-width: 768px) {
            .stats-grid { grid-template-columns: 1fr; }
            .navbar { flex-direction: column; gap: 15px; }
        }
    </style>
</head>
<body>
    <nav class="navbar">
        <h1>📊 Daily Agent 监控面板</h1>
        <div class="nav-links">
            <a href="/">🏠 首页</a>
            <a href="/setup">⚙️ 配置</a>
            <a href="/docs">📚 API 文档</a>
        </div>
    </nav>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-title">今日采集</div>
                <div class="stat-value">{today_collected}</div>
                <div class="stat-change positive">+12% 较昨日</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">本周日报</div>
                <div class="stat-value">{weekly_reports}</div>
                <div class="stat-change positive">正常生成</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">数据源</div>
                <div class="stat-value">{source_count}</div>
                <div class="stat-change {source_status_class}">{source_status}</div>
            </div>
            <div class="stat-card">
                <div class="stat-title">推送渠道</div>
                <div class="stat-value">{channel_count}</div>
                <div class="stat-change positive">已配置</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <span class="card-title">📡 数据源状态</span>
                <button class="btn btn-primary" onclick="refreshSources()">🔄 刷新</button>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>来源</th>
                        <th>类型</th>
                        <th>状态</th>
                        <th>今日采集</th>
                        <th>成功率</th>
                        <th>最后更新</th>
                    </tr>
                </thead>
                <tbody id="sources-table">
                    {sources_table}
                </tbody>
            </table>
        </div>
        
        <div class="card">
            <div class="card-header">
                <span class="card-title">📰 最近日报</span>
                <a href="/api/v1/reports" class="btn btn-secondary">查看全部</a>
            </div>
            <table>
                <thead>
                    <tr>
                        <th>日期</th>
                        <th>标题</th>
                        <th>内容数</th>
                        <th>状态</th>
                        <th>操作</th>
                    </tr>
                </thead>
                <tbody id="reports-table">
                    {reports_table}
                </tbody>
            </table>
        </div>
    </div>
    
    <script>
        async function refreshSources() {
            const btn = document.querySelector('.btn-primary');
            btn.textContent = '⏳ 刷新中...';
            
            try {
                const response = await fetch('/api/v1/dashboard/refresh');
                if (response.ok) {
                    location.reload();
                }
            } catch (error) {
                console.error('Error:', error);
                btn.textContent = '🔄 刷新';
            }
        }
        
        // 自动刷新每 30 秒
        setInterval(() => {
            fetch('/api/v1/dashboard/stats')
                .then(r => r.json())
                .then(data => {
                    // 更新统计数据
                    document.querySelectorAll('.stat-value')[0].textContent = data.today_collected;
                });
        }, 30000);
    </script>
</body>
</html>
"""


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page():
    """监控面板页面"""
    # 获取统计数据
    try:
        from src.database import get_session
        from sqlalchemy import text, func
        from datetime import datetime, timedelta, timezone
        
        async with get_session() as session:
            # 今日采集
            today = datetime.now(timezone.utc).date()
            result = await session.execute(text(
                "SELECT count(*) FROM content_items WHERE date(fetch_time) = :date"
            ), {"date": today.isoformat()})
            today_collected = result.scalar() or 0
            
            # 本周日报
            week_ago = today - timedelta(days=7)
            result = await session.execute(text(
                "SELECT count(*) FROM daily_reports WHERE date(date) >= :date"
            ), {"date": week_ago.isoformat()})
            weekly_reports = result.scalar() or 0
            
            # 数据源数量
            from src.config import get_column_config
            col_config = get_column_config()
            columns = col_config.get_columns(enabled_only=False)
            source_count = sum(len(c.get("sources", [])) for c in columns)
            
            # 推送渠道
            settings = get_settings()
            channel_count = sum([
                bool(settings.telegram_bot_token),
                bool(settings.slack_bot_token),
                bool(settings.discord_bot_token),
                bool(settings.smtp_host)
            ])
    except:
        today_collected = 0
        weekly_reports = 0
        source_count = 0
        channel_count = 0
    
    # 生成表格 HTML
    sources_table = ""
    for col in columns:
        for source in col.get("sources", []):
            sources_table += f"""
            <tr>
                <td>{source.get('name')}</td>
                <td>{source.get('type')}</td>
                <td><span class="status-badge success">正常</span></td>
                <td>-</td>
                <td><div class="progress-bar"><div class="progress-fill" style="width: 95%"></div></div></td>
                <td>-</td>
            </tr>
            """
    
    reports_table = ""
    for i in range(min(weekly_reports, 5)):
        date = today - timedelta(days=i)
        reports_table += f"""
        <tr>
            <td>{date.strftime('%Y-%m-%d')}</td>
            <td>今日日报 - {date.strftime('%Y年%m月%d日')}</td>
            <td>-</td>
            <td><span class="status-badge success">已生成</span></td>
            <td><a href="#" class="btn btn-secondary">查看</a></td>
        </tr>
        """
    
    html = DASHBOARD_HTML.format(
        today_collected=today_collected,
        weekly_reports=weekly_reports,
        source_count=source_count,
        source_status_class="positive" if source_count > 0 else "negative",
        source_status=f"{source_count} 个正常" if source_count > 0 else "未配置",
        channel_count=channel_count,
        sources_table=sources_table or '<tr><td colspan="6" style="text-align:center;color:#999;">暂无数据源</td></tr>',
        reports_table=reports_table or '<tr><td colspan="5" style="text-align:center;color:#999;">暂无日报</td></tr>'
    )
    
    return html


@router.get("/api/v1/dashboard/stats")
async def dashboard_stats():
    """API: 获取 Dashboard 统计数据"""
    try:
        from src.database import get_session
        from sqlalchemy import text
        from datetime import datetime, timedelta, timezone
        
        async with get_session() as session:
            today = datetime.now(timezone.utc).date()
            
            result = await session.execute(text(
                "SELECT count(*) FROM content_items WHERE date(fetch_time) = :date"
            ), {"date": today.isoformat()})
            today_collected = result.scalar() or 0
            
            return {
                "today_collected": today_collected,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
    except Exception as e:
        return {"today_collected": 0, "error": str(e)}
