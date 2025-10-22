#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Health Monitor Log Viewer
JSONログファイルを読み込んで美しいHTMLダッシュボードを生成するツール
"""

import json
import os
import glob
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse


class HealthLogViewer:
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
    
    def get_status_history(self, entries: List[Dict[str, Any]], hours: int = 24) -> Dict[str, List[Dict[str, Any]]]:
        """指定時間内のステータス履歴を取得"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        history = {}
        
        for entry in entries:
            if entry['parsed_timestamp'] < cutoff_time:
                continue
                
            target_name = entry.get('target_name')
            if target_name and target_name != 'system':
                if target_name not in history:
                    history[target_name] = []
                
                history[target_name].append({
                    'timestamp': entry['parsed_timestamp'],
                    'status_change': entry.get('status_change'),
                    'details': entry.get('details'),
                    'type': entry.get('target_type')
                })
        
        # 各ターゲットの履歴を時系列順にソート
        for target_name in history:
            history[target_name].sort(key=lambda x: x['timestamp'])
        
        return history
    
    def generate_html_dashboard(self, output_file: str = "dashboard.html", days: int = 1):
        """HTMLダッシュボードを生成"""
        # 指定日数分のログファイルを処理
        all_entries = []
        log_files = self.get_log_files()
        
        for log_file in log_files[:days]:  # 最新のN日分
            entries = self.parse_log_file(log_file)
            all_entries.extend(entries)
        
        # 時系列順にソート
        all_entries.sort(key=lambda x: x['parsed_timestamp'], reverse=True)
        
        # データを分析
        latest_status = self.get_latest_status(all_entries)
        history = self.get_status_history(all_entries, hours=24 * days)
        
        # HTMLを生成
        html_content = self._generate_html_content(latest_status, history, all_entries[:100])  # 最新100件
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"HTMLダッシュボードを生成しました: {output_file}")
    
    def _generate_html_content(self, latest_status: Dict, history: Dict, recent_entries: List) -> str:
        """HTML内容を生成"""
        
        # ステータス別の統計
        status_counts = {'up': 0, 'down': 0, 'unknown': 0, 'shutdown': 0}
        website_count = 0
        database_count = 0
        
        for target, info in latest_status.items():
            status = info['status']
            if status in status_counts:
                status_counts[status] += 1
            
            if info['type'] == 'website':
                website_count += 1
            elif info['type'] == 'database':
                database_count += 1
        
        # 現在時刻
        current_time = datetime.now().strftime('%Y年%m月%d日 %H:%M:%S')
        
        html = f"""
<!DOCTYPE html>
<html lang="ja">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ヘルスモニター - ステータスダッシュボード</title>
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
            max-width: 1200px;
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
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: rgba(255, 255, 255, 0.95);
            padding: 25px;
            border-radius: 15px;
            text-align: center;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
        }}
        
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            margin-bottom: 10px;
        }}
        
        .stat-label {{
            color: #7f8c8d;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .status-up {{ color: #27ae60; }}
        .status-down {{ color: #e74c3c; }}
        .status-unknown {{ color: #f39c12; }}
        .status-shutdown {{ color: #95a5a6; }}
        
        .main-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
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
        }}
        
        .service-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 15px;
            margin-bottom: 10px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #ddd;
        }}
        
        .service-item.up {{ border-left-color: #27ae60; }}
        .service-item.down {{ border-left-color: #e74c3c; }}
        .service-item.unknown {{ border-left-color: #f39c12; }}
        .service-item.shutdown {{ border-left-color: #95a5a6; }}
        
        .service-name {{
            font-weight: 600;
            color: #2c3e50;
        }}
        
        .service-type {{
            font-size: 0.8em;
            color: #7f8c8d;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .service-status {{
            display: flex;
            align-items: center;
            gap: 10px;
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
        
        .response-time {{
            font-size: 0.9em;
            color: #7f8c8d;
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
        
        @media (max-width: 768px) {{
            .main-grid {{
                grid-template-columns: 1fr;
            }}
            
            .stats-grid {{
                grid-template-columns: repeat(2, 1fr);
            }}
            
            .header h1 {{
                font-size: 2em;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏥 ヘルスモニター</h1>
            <div class="subtitle">ステータスダッシュボード - {current_time}</div>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number status-up">{status_counts['up']}</div>
                <div class="stat-label">正常稼働</div>
            </div>
            <div class="stat-card">
                <div class="stat-number status-down">{status_counts['down']}</div>
                <div class="stat-label">障害発生</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{website_count}</div>
                <div class="stat-label">Webサイト</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{database_count}</div>
                <div class="stat-label">データベース</div>
            </div>
        </div>
        
        <div class="main-grid">
            <div class="panel">
                <h2>🌐 現在のステータス</h2>
"""
        
        # 現在のステータス一覧
        for target_name, info in sorted(latest_status.items()):
            status = info['status']
            service_type = info['type']
            response_time = info.get('response_time')
            
            response_time_text = ""
            if response_time is not None:
                response_time_text = f'<span class="response-time">({response_time:.2f}s)</span>'
            
            html += f"""
                <div class="service-item {status}">
                    <div>
                        <div class="service-name">{target_name}</div>
                        <div class="service-type">{service_type}</div>
                    </div>
                    <div class="service-status">
                        <span class="status-badge {status}">{status}</span>
                        {response_time_text}
                    </div>
                </div>
"""
        
        html += """
            </div>
            
            <div class="panel">
                <h2>📊 最新のログ</h2>
"""
        
        # 最新のログエントリ
        for entry in recent_entries[:10]:  # 最新10件
            timestamp = entry['parsed_timestamp'].strftime('%H:%M:%S')
            target_name = entry.get('target_name', 'Unknown')
            status_change = entry.get('status_change', '')
            details = entry.get('details', '')
            
            # 詳細を短縮
            if len(details) > 100:
                details = details[:100] + "..."
            
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
            このダッシュボードは手動で更新されます。最新の情報を確認するには、ログビューアーを再実行してください。
        </div>
    </div>
</body>
</html>
"""
        
        return html


def main():
    parser = argparse.ArgumentParser(description='Health Monitor Log Viewer')
    parser.add_argument('--log-dir', default='logs', help='ログディレクトリのパス (デフォルト: logs)')
    parser.add_argument('--output', default='dashboard.html', help='出力HTMLファイル名 (デフォルト: dashboard.html)')
    parser.add_argument('--days', type=int, default=1, help='表示する日数 (デフォルト: 1)')
    
    args = parser.parse_args()
    
    viewer = HealthLogViewer(args.log_dir)
    viewer.generate_html_dashboard(args.output, args.days)


if __name__ == "__main__":
    main()