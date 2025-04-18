import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np
import pandas as pd
import os
import matplotlib.font_manager as fm
import subprocess
import sys

subprocess.run(['fc-cache', '-fv'])

font_list = fm.findSystemFonts(fontpaths=None, fontext='ttf')
japanese_fonts = [f for f in font_list if any(name in f.lower() for name in ['ipa', 'gothic', 'mincho', 'vlgothic'])]

if japanese_fonts:
    print(f"Found Japanese fonts: {japanese_fonts}")
    for font_path in japanese_fonts:
        fm.fontManager.addfont(font_path)
    
    plt.rcParams['font.family'] = ['IPAexGothic', 'IPAGothic', 'VL Gothic', 'Noto Sans CJK JP', 'DejaVu Sans', 'sans-serif']
else:
    print("No Japanese fonts found. Using default fonts.")
    plt.rcParams['font.family'] = ['DejaVu Sans', 'sans-serif']

plt.rcParams['axes.unicode_minus'] = False

class FinancialVisualizer:
    def __init__(self, financial_data, company_name="エピック"):
        """
        Initialize the visualizer with financial data.
        
        Args:
            financial_data: DataFrame with financial data for multiple periods
            company_name: Name of the company
        """
        self.data = financial_data
        self.company_name = company_name
        self.periods = sorted(financial_data.index.astype(str))
        
        self.colors = {
            'blue': '#A8C8E6',      # Assets, Revenue
            'light_blue': '#D6E6F5', 
            'green': '#C5E0B4',     # Profits, Equity
            'light_green': '#E2F0D9',
            'orange': '#F8CBAD',    # Expenses, Liabilities
            'light_orange': '#FCE4D6',
            'yellow': '#FFF2CC',
            'white': '#FFFFFF',
            'gray': '#F2F2F2',
            'border': '#000000'
        }
        
        self.fig = plt.figure(figsize=(16.5, 11.7))  # A3 size in inches
        self.fig.patch.set_facecolor('white')
        
    def format_number(self, value, include_comma=True):
        """Format numbers for display."""
        if pd.isna(value) or value == 0:
            return ""
        
        if isinstance(value, (int, float)):
            if value >= 1000000:
                formatted = f"{value/1000000:.1f}"
            else:
                formatted = f"{value:.0f}"
                
            if include_comma:
                parts = formatted.split('.')
                parts[0] = "{:,}".format(float(parts[0]))
                formatted = '.'.join(parts)
            
            return formatted
        return str(value)
    
    def format_percentage(self, value):
        """Format percentage values."""
        if pd.isna(value) or value == 0:
            return ""
        return f"{value:.1f}%"
    
    def draw_text_box(self, ax, x, y, width, height, text, fontsize=9, 
                     color='white', text_color='black', alpha=1.0, 
                     ha='center', va='center', border=True, border_color='black'):
        """Draw a text box with optional border."""
        rect = patches.Rectangle((x, y), width, height, linewidth=1 if border else 0, 
                                edgecolor=border_color if border else color, 
                                facecolor=color, alpha=alpha)
        ax.add_patch(rect)
        
        ax.text(x + width/2, y + height/2, text, fontsize=fontsize,
               color=text_color, ha=ha, va=va)
        
    def draw_pl_section(self, ax, period_idx, period, x_start, width):
        """Draw the P/L (Profit/Loss) section for a specific period."""
        if period not in self.data.index:
            return
            
        period_data = self.data.loc[period]
        
        fiscal_year = f"第{period}期"
        date_range = f"令和{int(period)-3}年4月1日～令和{int(period)-2}年3月31日"
        unit = "単位：千円"
        
        self.draw_text_box(ax, x_start, 0.9, width, 0.05, fiscal_year, fontsize=10, color='white')
        self.draw_text_box(ax, x_start, 0.85, width*0.7, 0.05, date_range, fontsize=8, color='white')
        self.draw_text_box(ax, x_start + width*0.7, 0.85, width*0.3, 0.05, unit, fontsize=8, color='white')
        
        sales_value = period_data.get('売上高', 0)
        sales_formatted = self.format_number(sales_value)
        
        self.draw_text_box(ax, x_start, 0.65, width*0.3, 0.2, 
                          f"売上高\n{sales_formatted}", 
                          color=self.colors['blue'])
        
        gross_profit = period_data.get('売上総利益', 0)
        gross_profit_ratio = (gross_profit / sales_value * 100) if sales_value else 0
        
        self.draw_text_box(ax, x_start + width*0.3, 0.65, width*0.7, 0.2, 
                          f"売上総利益\n{self.format_number(gross_profit)}\n{self.format_percentage(gross_profit_ratio)}", 
                          color=self.colors['green'])
        
        sga = period_data.get('販売費及び一般管理費', 0)
        sga_ratio = (sga / sales_value * 100) if sales_value else 0
        
        self.draw_text_box(ax, x_start + width*0.3, 0.55, width*0.7, 0.1, 
                          f"販売費・一般管理費\n{self.format_number(sga)}", 
                          color=self.colors['gray'])
        
        operating_profit = period_data.get('営業利益', 0)
        operating_profit_ratio = (operating_profit / sales_value * 100) if sales_value else 0
        
        financial_income = period_data.get('営業外収益', 0) 
        financial_expenses = period_data.get('営業外費用', 0)
        
        ordinary_profit = period_data.get('経常利益', 0)
        ordinary_profit_ratio = (ordinary_profit / sales_value * 100) if sales_value else 0
        
        extraordinary_income = period_data.get('特別利益', 0)
        extraordinary_expenses = period_data.get('特別損失', 0)
        
        profit_before_tax = period_data.get('税引前当期純利益', 0)
        
        income_taxes = period_data.get('法人税等', 0)
        
        net_profit = period_data.get('当期純利益', 0)
        net_profit_ratio = (net_profit / sales_value * 100) if sales_value else 0
        
        y_pos = 0.45
        height = 0.1
        self.draw_text_box(ax, x_start, y_pos, width*0.3, height, 
                          f"営業利益率\n{self.format_percentage(operating_profit_ratio)}", 
                          color=self.colors['light_orange'])
        
        small_width = width*0.175
        self.draw_text_box(ax, x_start + width*0.3, y_pos, small_width, height, 
                          f"営業利益\n{self.format_percentage(operating_profit_ratio)}", 
                          color=self.colors['light_green'])
        
        self.draw_text_box(ax, x_start + width*0.3 + small_width, y_pos, small_width, height, 
                          f"経常利益\n{self.format_percentage(ordinary_profit_ratio)}", 
                          color=self.colors['light_green'])
        
        self.draw_text_box(ax, x_start + width*0.3 + small_width*2, y_pos, small_width, height, 
                          f"特別損益\n{self.format_number(extraordinary_income - extraordinary_expenses)}", 
                          color=self.colors['light_green'])
        
        self.draw_text_box(ax, x_start + width*0.3 + small_width*3, y_pos, small_width, height, 
                          f"当期純利益\n{self.format_number(net_profit)}", 
                          color=self.colors['orange'])
        
    def draw_bs_section(self, ax, period_idx, period, x_start, width):
        """Draw the B/S (Balance Sheet) section for a specific period."""
        if period not in self.data.index:
            return
            
        period_data = self.data.loc[period]
        
        fiscal_year = f"第{period}期"
        date = f"令和{int(period)-2}年3月31日"
        unit = "単位：千円"
        
        self.draw_text_box(ax, x_start, 0.45, width, 0.05, fiscal_year, fontsize=10, color='white')
        self.draw_text_box(ax, x_start, 0.4, width*0.7, 0.05, date, fontsize=8, color='white')
        self.draw_text_box(ax, x_start + width*0.7, 0.4, width*0.3, 0.05, unit, fontsize=8, color='white')
        
        total_assets = period_data.get('資産合計', 0)
        current_assets = period_data.get('流動資産合計', 0)
        fixed_assets = period_data.get('固定資産合計', 0)
        
        cash = period_data.get('現金及び預金', 0)
        
        accounts_receivable = period_data.get('売掛金等', 0)
        
        current_assets_ratio = (current_assets / total_assets * 100) if total_assets else 0
        
        assets_height = 0.25
        self.draw_text_box(ax, x_start, 0.15, width*0.3, assets_height, 
                          f"流動・固定\n{self.format_number(current_assets)}", 
                          color=self.colors['blue'])
        
        assets_breakdown_width = width*0.1
        self.draw_text_box(ax, x_start + width*0.3, 0.15, assets_breakdown_width, assets_height, 
                          f"流動資産比率\n{self.format_percentage(current_assets_ratio)}", 
                          color=self.colors['light_blue'])
        
        self.draw_text_box(ax, x_start + width*0.3 + assets_breakdown_width, 0.15, 
                          assets_breakdown_width, assets_height*0.5, 
                          f"現金・預金\n{self.format_number(cash)}", 
                          color=self.colors['light_blue'])
        
        self.draw_text_box(ax, x_start + width*0.3 + assets_breakdown_width, 0.15 + assets_height*0.5, 
                          assets_breakdown_width, assets_height*0.5, 
                          f"売掛金等\n{self.format_number(accounts_receivable)}", 
                          color=self.colors['light_blue'])
        
        total_liabilities = period_data.get('負債合計', 0)
        current_liabilities = period_data.get('流動負債合計', 0)
        fixed_liabilities = period_data.get('固定負債合計', 0) if '固定負債合計' in period_data else 0
        total_equity = period_data.get('純資産合計', 0)
        
        equity_ratio = (total_equity / total_assets * 100) if total_assets else 0
        
        liabilities_width = width*0.5
        self.draw_text_box(ax, x_start + width*0.5, 0.15, liabilities_width, assets_height*0.3, 
                          f"負債の部\n{self.format_number(total_liabilities)}", 
                          color=self.colors['green'])
        
        self.draw_text_box(ax, x_start + width*0.5, 0.15 + assets_height*0.3, liabilities_width, assets_height*0.7, 
                          f"純資産の部\n{self.format_number(total_equity)}\n{self.format_percentage(equity_ratio)}", 
                          color=self.colors['green'])
        
        self.draw_text_box(ax, x_start, 0.05, width*0.3, 0.1, 
                          f"資産合計\n{self.format_number(total_assets)}", 
                          color=self.colors['light_blue'])
        
        self.draw_text_box(ax, x_start + width*0.5, 0.05, width*0.5, 0.1, 
                          f"負債・純資産合計\n{self.format_number(total_liabilities + total_equity)}", 
                          color=self.colors['light_green'])
        
    def create_visualization(self, output_path):
        """Create the complete financial visualization."""
        ax_pl = self.fig.add_subplot(211)
        ax_bs = self.fig.add_subplot(212)
        
        ax_pl.axis('off')
        ax_bs.axis('off')
        
        ax_pl.set_xlim(0, 1)
        ax_pl.set_ylim(0, 1)
        ax_bs.set_xlim(0, 1)
        ax_bs.set_ylim(0, 1)
        
        self.fig.suptitle(f"{self.company_name} 様", fontsize=16, y=0.98)
        
        ax_pl.text(0.05, 0.5, "P/L", fontsize=14, color='white', 
                  bbox=dict(facecolor='black', alpha=1.0))
        ax_bs.text(0.05, 0.5, "B/S", fontsize=14, color='white', 
                  bbox=dict(facecolor='black', alpha=1.0))
        
        num_periods = len(self.periods)
        width = 0.9 / num_periods
        
        for i, period in enumerate(self.periods):
            x_start = 0.1 + i * width
            self.draw_pl_section(ax_pl, i, period, x_start, width)
            self.draw_bs_section(ax_bs, i, period, x_start, width)
        
        plt.figtext(0.5, 0.02, f"作成日：{pd.Timestamp.now().strftime('%Y年%m月%d日')}", 
                   ha='center', fontsize=8)
        plt.figtext(0.95, 0.02, "Copyright© 2023 Interfirm Business Succession Consulting Association All right reserved", 
                   ha='right', fontsize=6)
        
        plt.tight_layout(rect=(0, 0.03, 1, 0.97))
        
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"Financial visualization saved to {output_path}")
        
        return self.fig
