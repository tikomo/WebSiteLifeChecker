#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Advanced Health Monitor Log Viewer
自動更新機能付きの高度なHTMLダッシュボードを生成するツール
"""

import json
import os
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse


class AdvancedHealthLogViewer:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        
    def get_log_files(self) -> List[str]:
        """ログディレクトリから全てのログファイルを取得"""
        pattern = os.path.join(self.log_dir, "health_monitor_*.log")
        return sorted(glob.glob(pattern), reverse=True)
    
    def parse_log_file(self, log_file: str) -> List[Dict[str, Any]]:
        """JSONログファイルを解析"""
        entries = []
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line:
                        try:
                            entry = json.loads(line)
                            # タイムスタンプを解析
                            entry['parsed_timestamp'] = datetime.fromisoformat(
                                entry['timestamp'].replace('Z', '+00:00')
                            )
                            entries.append(entry)
                        except json.JSONDecodeError:
                            continue
        except FileNotFoundError:
            print(f"ログファイルが見つかりません: {log_file}")
        
        return entries
    
    def get_latest_status(self, entries: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """各監視対象の最新ステータスを取得"""
        latest_status = {}
        
        for entry in entries:
            target_name = entry.get('target_name')
            if target_name and target_name != 'system':
                # ステータス変更を解析
                status_change = entry.get('status_change', '')
                if '->' in status_change:
                    current_status = status_change.split('->')[-1]
                else:
                    current_status = status_change
                
                # 応答時間を抽出
                response_time = None
                details = entry.get('details', '')
                if 'Response time:' in details:
                    try:
                        time_str = details.split('Response time: ')[1].split('s')[0]
                        response_time = float(time_str)
                    except (IndexError, ValueError):
                        pass
                
                latest_status[target_name] = {
                    'status': current_status,
                    'type': entry.get('target_type'),
                    'timestamp': entry['parsed_timestamp'],
                    'details': details,
                    'response_time': response_time
                }
        
        return latest_status
    
    def get_uptime_stats(self, entries: List[Dict[str, Any]], hours: int = 24) -> Dict[str, Dict[str, Any]]:
        """稼働率統計を計算"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        uptime_stats = {}
        
        # 各ターゲットの状態変化を追跡
        for entry in entries:
            if entry['parsed_timestamp'] < cutoff_time:
                continue
                
            target_name = entry.get('target_name')
            if target_name and target_name != 'system':
                if target_name not in uptime_stats:
                    uptime_stats[target_name] = {
                        'total_checks': 0,
                        'up_checks': 0,
                        'down_checks': 0,
                        'response_times': []
                    }
                
                status_change = entry.get('status_change', '')
                current_status = status_change.split('->')[-1] if '->' in status_change else status_change
                
                uptime_stats[target_name]['total_checks'] += 1
                
                if current_status == 'up':
                    uptime_stats[target_name]['up_checks'] += 1
                elif current_status == 'down':
                    uptime_stats[target_name]['down_checks'] += 1
                
                # 応答時間を記録
                details = entry.get('details', '')
                if 'Response time:' in details:
                    try:
                        time_str = details.split('Response time: ')[1].split('s')[0]
                        response_time = float(time_str)
                        uptime_stats[target_name]['response_times'].append(response_time)
                    except (IndexError, ValueError):
                        pass
        
        # 稼働率を計算
        for target_name in uptime_stats:
            stats = uptime_stats[target_name]
            if stats['total_checks'] > 0:
                stats['uptime_percentage'] = (stats['up_checks'] / stats['total_checks']) * 100
            else:
                stats['uptime_percentage'] = 0
            
            # 平均応答時間を計算
            if stats['response_times']:
                stats['avg_response_time'] = sum(stats['response_times']) / len(stats['response_times'])
                stats['max_response_time'] = max(stats['response_times'])
                stats['min_response_time'] = min(stats['response_times'])
            else:
                stats['avg_response_time'] = None
                stats['max_response_time'] = None
                stats['min_response_time'] = None
        
        return uptime_stats
    
    def generate_advanced_dashboard(self, output_file: str = "advanced_dashboard.html", days: int = 1):
        """高度なHTMLダッシュボードを生成"""
        # 指定日数分のログファイルを処理
        all_entries = []
        log_files = self.get_log_files()
        
        for log_file in log_files[:days]:
            entries = self.parse_log_file(log_file)
            all_entries.extend(entries)
        
        # 時系列順にソート
        all_entries.sort(key=lambda x: x['parsed_timestamp'], reverse=True)
        
        # データを分析
        latest_status = self.get_latest_status(all_entries)
        uptime_stats = self.get_uptime_stats(all_entries, hours=24 * days)
        
        # HTMLを生成
        html_content = self._generate_advanced_html_content(latest_status, uptime_stats, all_entries[:50])
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"高度なHTMLダッシュボードを生成しました: {output_file}")
    
    def _generate_advanced_html_content(self, latest_status: Dict, uptime_stats: Dict, recent_entries: List) -> str:
        """高度なHTML内容を生成"""
        
        # 統計情報を計算
        total_services = len(latest_status)
        up_services = sum(1 for info in latest_status.values() if info['status'] == 'up')
        down_services = sum(1 for info in latest_status.values() if info['status'] == 'down')
        
        overall_uptime = (up_services / total_services * 100) if total_services > 0 else 0
        
        current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Health Monitor - 高度なダッシュボード</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            background: rgba(255, 255, 255, 0.95);
            padding: 30px;
            border-radius: 15px;
            margin-bottom: 30px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            text-align: center;
            position: relative;
        }}
        
        .header h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }}
        
        .header .subtitle {{
            color: #7f8c8d;
            font-size: 1.1em;
        }}
        
        .auto-refresh {{
            position: absolute;
            top: 20px;
            right: 20px;
            background: #3498db;
            color: white;
            padding: 10px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            cursor: pointer;
            transition: background 0.3s;
        }}
        
        .auto-refresh:hover {{
            background: #2980b9;
        }}
        
        .auto-refresh.active {{
            background: #27ae60;
        }}
        
        .overview-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .overview-card {{
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }}
        
        .overview-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .overview-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .uptime-good {{ color: #27ae60; }}
        .uptime-warning {{ color: #f39c12; }}
        .uptime-critical {{ color: #e74c3c; }}
        
        .main-content {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
            margin-bottom: 30px;
        }}
        
        .panel {{
            background: rgba(255, 255, 255, 0.95);
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }}
        
        .panel h2 {{
            color: #2c3e50;
            margin-bottom: 20px;
            font-size: 1.5em;
            font-weight: 400;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .service-grid {{
            display: grid;
            gap: 15px;
        }}
        
        .service-card {{
            background: #f8f9fa;
            border-radius: 10px;
            padding: 20px;
            border-left: 4px solid #ddd;
            transition: transform 0.2s, box-shadow 0.2s;
        }}
        
        .service-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        }}
        
        .service-card.up {{ border-left-color: #27ae60; }}
        .service-card.down {{ border-left-color: #e74c3c; }}
        .service-card.unknown {{ border-left-color: #f39c12; }}
        .service-card.shutdown {{ border-left-color: #95a5a6; }}
        
        .service-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        
        .service-name {{
            font-weight: 600;
            color: #2c3e50;
            font-size: 1.1em;
        }}
        
        .service-type {{
            font-size: 0.8em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .status-badge {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8em;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .status-badge.up {{
            background: #d5f4e6;
            color: #27ae60;
        }}
        
        .status-badge.down {{
            background: #fdeaea;
            color: #e74c3c;
        }}
        
        .status-badge.unknown {{
            background: #fef9e7;
            color: #f39c12;
        }}
        
        .status-badge.shutdown {{
            background: #f4f4f4;
            color: #95a5a6;
        }}
        
        .service-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(100px, 1fr));
            gap: 10px;
            margin-top: 15px;
        }}
        
        .stat-item {{
            text-align: center;
            padding: 10px;
            background: white;
            border-radius: 8px;
        }}
        
        .stat-value {{
            font-weight: bold;
            color: #2c3e50;
            font-size: 1.1em;
        }}
        
        .stat-label {{
            font-size: 0.8em;
            color: #7f8c8d;
            margin-top: 5px;
        }}
        
        .log-entry {{
            padding: 15px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #3498db;
        }}
        
        .log-timestamp {{
            font-size: 0.8em;
            color: #7f8c8d;
            margin-bottom: 5px;
        }}
        
        .log-target {{
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 5px;
        }}
        
        .log-details {{
            font-size: 0.9em;
            color: #5a6c7d;
            word-break: break-word;
        }}
        
        .refresh-info {{
            text-align: center;
            color: rgba(255, 255, 255, 0.8);
            margin-top: 20px;
            font-size: 0.9em;
        }}
        
        @media (max-width: 1024px) {{
            .main-content {{
                grid-template-columns: 1fr;
            }}
            
            .overview-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
        
        @media (max-width: 768px) {{
            .overview-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
            
            .auto-refresh {{
                position: static;
                margin-top: 15px;
                display: inline-block;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div class="auto-refresh" onclick="toggleAutoRefresh()">🔄 自動更新: OFF</div>
            <h1>🏥 Health Monitor</h1>
            <div class="subtitle">高度なステータスダッシュボード - {current_time}</div>
        </div>
        
        <div class="overview-grid">
            <div class="overview-card">
                <div class="overview-number uptime-{'good' if overall_uptime >= 95 else 'warning' if overall_uptime >= 90 else 'critical'}">{overall_uptime:.1f}%</div>
                <div class="overview-label">全体稼働率</div>
            </div>
            <div class="overview-card">
                <div class="overview-number uptime-good">{up_services}</div>
                <div class="overview-label">正常稼働</div>
            </div>
            <div class="overview-card">
                <div class="overview-number uptime-critical">{down_services}</div>
                <div class="overview-label">障害発生</div>
            </div>
            <div class="overview-card">
                <div class="overview-number">{total_services}</div>
                <div class="overview-label">総監視対象</div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="panel">
                <h2>🎯 サービス詳細ステータス</h2>
                <div class="service-grid">
"""
        
        # サービス詳細カード
        for target_name, info in sorted(latest_status.items()):
            status = info['status']
            service_type = info['type']
            response_time = info.get('response_time')
            
            # 稼働率統計を取得
            stats = uptime_stats.get(target_name, {})
            uptime_pct = stats.get('uptime_percentage', 0)
            avg_response = stats.get('avg_response_time')
            
            html += f"""
                    <div class="service-card {status}">
                        <div class="service-header">
                            <div>
                                <div class="service-name">{target_name}</div>
                                <div class="service-type">{service_type}</div>
                            </div>
                            <span class="status-badge {status}">{status}</span>
                        </div>
                        <div class="service-stats">
                            <div class="stat-item">
                                <div class="stat-value">{uptime_pct:.1f}%</div>
                                <div class="stat-label">稼働率</div>
                            </div>
"""
            
            if response_time is not None:
                html += f"""
                            <div class="stat-item">
                                <div class="stat-value">{response_time:.2f}s</div>
                                <div class="stat-label">現在の応答</div>
                            </div>
"""
            
            if avg_response is not None:
                html += f"""
                            <div class="stat-item">
                                <div class="stat-value">{avg_response:.2f}s</div>
                                <div class="stat-label">平均応答</div>
                            </div>
"""
            
            html += """
                        </div>
                    </div>
"""
        
        html += """
                </div>
            </div>
            
            <div class="panel">
                <h2>📊 最新アクティビティ</h2>
"""
        
        # 最新のログエントリ
        for entry in recent_entries[:15]:
            timestamp = entry['parsed_timestamp'].strftime('%H:%M:%S')
            target_name = entry.get('target_name', 'Unknown')
            status_change = entry.get('status_change', '')
            details = entry.get('details', '')
            
            # 詳細を短縮
            if len(details) > 80:
                details = details[:80] + "..."
            
            html += f"""
                <div class="log-entry">
                    <div class="log-timestamp">{timestamp}</div>
                    <div class="log-target">{target_name} - {status_change}</div>
                    <div class="log-details">{details}</div>
                </div>
"""
        
        html += """
            </div>
        </div>
        
        <div class="refresh-info">
            <div id="refresh-status">手動更新モード - 最新情報を確認するには、ページを再読み込みしてください</div>
        </div>
    </div>
    
    <script>
        let autoRefreshEnabled = false;
        let refreshInterval;
        
        function toggleAutoRefresh() {
            const button = document.querySelector('.auto-refresh');
            const status = document.getElementById('refresh-status');
            
            autoRefreshEnabled = !autoRefreshEnabled;
            
            if (autoRefreshEnabled) {
                button.textContent = '🔄 自動更新: ON';
                button.classList.add('active');
                status.textContent = '自動更新モード - 30秒ごとに更新されます';
                
                refreshInterval = setInterval(() => {
                    location.reload();
                }, 30000);
            } else {
                button.textContent = '🔄 自動更新: OFF';
                button.classList.remove('active');
                status.textContent = '手動更新モード - 最新情報を確認するには、ページを再読み込みしてください';
                
                if (refreshInterval) {
                    clearInterval(refreshInterval);
                }
            }
        }
        
        // ページ読み込み時の初期化
        document.addEventListener('DOMContentLoaded', function() {
            // 現在時刻を更新
            setInterval(() => {
                const now = new Date();
                const timeString = now.toLocaleString('ja-JP');
                document.querySelector('.subtitle').textContent = `高度なステータスダッシュボード - ${timeString}`;
            }, 1000);
        });
    </script>
</body>
</html>
"""
        
        return html


def main():
    parser = argparse.ArgumentParser(description='Advanced Health Monitor Log Viewer')
    parser.add_argument('--log-dir', default='logs', help='ログディレクトリのパス (デフォルト: logs)')
    parser.add_argument('--output', default='advanced_dashboard.html', help='出力HTMLファイル名 (デフォルト: advanced_dashboard.html)')
    parser.add_argument('--days', type=int, default=1, help='表示する日数 (デフォルト: 1)')
    
    args = parser.parse_args()
    
    viewer = AdvancedHealthLogViewer(args.log_dir)
    viewer.generate_advanced_dashboard(args.output, args.days)


if __name__ == "__main__":
    main()