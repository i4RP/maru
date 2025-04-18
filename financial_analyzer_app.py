import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import fitz  # PyMuPDF
import pandas as pd
import re
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import threading
import locale
from custom_visualization import FinancialVisualizer

try:
    locale.setlocale(locale.LC_ALL, 'ja_JP.UTF-8')
except:
    pass

plt.rcParams['font.family'] = ['IPAexGothic', 'IPAGothic', 'VL Gothic', 'DejaVu Sans']

class FinancialAnalyzerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("エピック_三期決算図 生成アプリ")
        self.root.geometry("1000x700")
        self.root.configure(bg="#f0f0f0")
        
        self.pdf_files = []
        self.financial_data = {}
        self.output_dir = os.path.expanduser("~")
        
        self.create_ui()
    
    def create_ui(self):
        main_frame = ttk.Frame(self.root, padding=10)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        title_label = ttk.Label(main_frame, text="三期決算図生成アプリ", font=("Arial", 16, "bold"))
        title_label.pack(pady=10)
        
        instructions = ttk.Label(main_frame, text="3つの決算書PDFファイルを選択して、三期決算図を生成します。", wraplength=800)
        instructions.pack(pady=5)
        
        file_frame = ttk.LabelFrame(main_frame, text="PDFファイル選択", padding=10)
        file_frame.pack(fill=tk.X, pady=10)
        
        select_button = ttk.Button(file_frame, text="PDFファイルを選択", command=self.select_files)
        select_button.pack(side=tk.LEFT, padx=5)
        
        self.files_label = ttk.Label(file_frame, text="選択されたファイル: 0", wraplength=700)
        self.files_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        output_frame = ttk.LabelFrame(main_frame, text="出力先フォルダ", padding=10)
        output_frame.pack(fill=tk.X, pady=10)
        
        output_button = ttk.Button(output_frame, text="出力先を選択", command=self.select_output_dir)
        output_button.pack(side=tk.LEFT, padx=5)
        
        self.output_label = ttk.Label(output_frame, text=f"出力先: {self.output_dir}", wraplength=700)
        self.output_label.pack(side=tk.LEFT, padx=10, fill=tk.X, expand=True)
        
        generate_button = ttk.Button(main_frame, text="三期決算図を生成", command=self.generate_charts)
        generate_button.pack(pady=10)
        
        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Progressbar(main_frame, variable=self.progress_var, maximum=100)
        self.progress.pack(fill=tk.X, pady=5)
        
        self.status_label = ttk.Label(main_frame, text="準備完了")
        self.status_label.pack(pady=5)
        
        preview_frame = ttk.LabelFrame(main_frame, text="プレビュー", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.canvas_frame = ttk.Frame(preview_frame)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.fig = Figure(figsize=(9, 5))
        self.canvas = FigureCanvasTkAgg(self.fig, self.canvas_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    def select_files(self):
        """Select PDF files for analysis."""
        files = filedialog.askopenfilenames(
            title="決算書PDFファイルを選択",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")]
        )
        
        if files:
            self.pdf_files = list(files)
            self.files_label.config(text=f"選択されたファイル: {len(self.pdf_files)}\n" + "\n".join(self.pdf_files))
            self.status_label.config(text=f"{len(self.pdf_files)}個のファイルが選択されました")
    
    def select_output_dir(self):
        """Select output directory for saving charts."""
        directory = filedialog.askdirectory(title="出力先フォルダを選択")
        if directory:
            self.output_dir = directory
            self.output_label.config(text=f"出力先: {self.output_dir}")
    
    def generate_charts(self):
        """Generate financial charts from the selected PDF files."""
        if len(self.pdf_files) < 1:
            messagebox.showerror("エラー", "PDFファイルを選択してください")
            return
        
        threading.Thread(target=self.process_files, daemon=True).start()
    
    def process_files(self):
        """Process PDF files and generate charts in a separate thread."""
        try:
            self.status_label.config(text="処理中...")
            self.progress_var.set(0)
            
            self.financial_data = {}
            for i, pdf_path in enumerate(self.pdf_files):
                self.status_label.config(text=f"PDFファイルを分析中: {os.path.basename(pdf_path)}")
                period = self.extract_period_from_filename(os.path.basename(pdf_path))
                if not period:
                    period = str(i + 1)
                
                text = self.extract_text_from_pdf(pdf_path)
                
                financial_data = self.extract_financial_data(text)
                self.financial_data[period] = financial_data
                
                self.progress_var.set((i + 1) / len(self.pdf_files) * 50)
            
            self.status_label.config(text="グラフを生成中...")
            df = self.create_financial_charts()
            
            csv_path = os.path.join(self.output_dir, "エピック_財務データ.csv")
            df.to_csv(csv_path)
            
            self.status_label.config(text="完了しました")
            self.progress_var.set(100)
            
            messagebox.showinfo("完了", f"三期決算図の生成が完了しました。\n出力先: {self.output_dir}")
            
        except Exception as e:
            self.status_label.config(text=f"エラーが発生しました: {str(e)}")
            messagebox.showerror("エラー", f"処理中にエラーが発生しました:\n{str(e)}")
    
    def extract_text_from_pdf(self, pdf_path):
        """Extract text from all pages of a PDF file."""
        doc = fitz.open(pdf_path)
        text = ""
        for page in doc:
            text += page.get_text()
        doc.close()
        return text
    
    def extract_period_from_filename(self, filename):
        """Extract the period number from the filename."""
        match = re.search(r'(\d+)期', filename)
        if match:
            return match.group(1)
        
        match = re.search(r'(\d+)\.pdf$', filename)
        if match:
            return match.group(1)
        
        return None
    
    def extract_financial_data(self, text):
        """Extract both balance sheet and income statement data from the text."""
        financial_data = {}
        
        
        cash_match = re.search(r'現金及び預金\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if cash_match:
            financial_data['現金及び預金'] = cash_match.group(1).replace(',', '')
        
        accounts_receivable_match = re.search(r'(受取手形|売掛金|完成工事未収入金)\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if accounts_receivable_match:
            financial_data['売掛金等'] = accounts_receivable_match.group(2).replace(',', '')
        
        inventory_match = re.search(r'(たな卸資産|商品|製品|仕掛品|原材料|貯蔵品|未成工事支出金)\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if inventory_match:
            financial_data['たな卸資産'] = inventory_match.group(2).replace(',', '')
        
        total_current_assets_match = re.search(r'流動資産合計\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if total_current_assets_match:
            financial_data['流動資産合計'] = total_current_assets_match.group(1).replace(',', '')
        
        fixed_assets_match = re.search(r'固定資産合計\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if fixed_assets_match:
            financial_data['固定資産合計'] = fixed_assets_match.group(1).replace(',', '')
        
        total_assets_match = re.search(r'資産合計\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if total_assets_match:
            financial_data['資産合計'] = total_assets_match.group(1).replace(',', '')
        
        accounts_payable_match = re.search(r'(支払手形|買掛金|工事未払金)\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if accounts_payable_match:
            financial_data['買掛金等'] = accounts_payable_match.group(2).replace(',', '')
        
        short_term_loans_match = re.search(r'短期借入金\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if short_term_loans_match:
            financial_data['短期借入金'] = short_term_loans_match.group(1).replace(',', '')
        
        total_current_liabilities_match = re.search(r'流動負債合計\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if total_current_liabilities_match:
            financial_data['流動負債合計'] = total_current_liabilities_match.group(1).replace(',', '')
        
        long_term_loans_match = re.search(r'長期借入金\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if long_term_loans_match:
            financial_data['長期借入金'] = long_term_loans_match.group(1).replace(',', '')
        
        total_fixed_liabilities_match = re.search(r'固定負債合計\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if total_fixed_liabilities_match:
            financial_data['固定負債合計'] = total_fixed_liabilities_match.group(1).replace(',', '')
        
        total_liabilities_match = re.search(r'負債合計\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if total_liabilities_match:
            financial_data['負債合計'] = total_liabilities_match.group(1).replace(',', '')
        
        capital_stock_match = re.search(r'資本金\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if capital_stock_match:
            financial_data['資本金'] = capital_stock_match.group(1).replace(',', '')
        
        retained_earnings_match = re.search(r'利益剰余金\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if retained_earnings_match:
            financial_data['利益剰余金'] = retained_earnings_match.group(1).replace(',', '')
        
        total_net_assets_match = re.search(r'純資産合計\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if total_net_assets_match:
            financial_data['純資産合計'] = total_net_assets_match.group(1).replace(',', '')
        
        sales_match = re.search(r'(売上高|完成工事高)\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if sales_match:
            financial_data['売上高'] = sales_match.group(2).replace(',', '')
        
        cost_of_sales_match = re.search(r'(売上原価|完成工事原価)\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if cost_of_sales_match:
            financial_data['売上原価'] = cost_of_sales_match.group(2).replace(',', '')
        
        gross_profit_match = re.search(r'売上総利益\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if gross_profit_match:
            financial_data['売上総利益'] = gross_profit_match.group(1).replace(',', '')
        
        sga_match = re.search(r'(販売費及び一般管理費|一般管理費)\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if sga_match:
            financial_data['販売費及び一般管理費'] = sga_match.group(2).replace(',', '')
        
        operating_profit_match = re.search(r'営業利益\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if operating_profit_match:
            financial_data['営業利益'] = operating_profit_match.group(1).replace(',', '')
        
        ordinary_profit_match = re.search(r'経常利益\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if ordinary_profit_match:
            financial_data['経常利益'] = ordinary_profit_match.group(1).replace(',', '')
        
        profit_before_tax_match = re.search(r'税引前当期純利益\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if profit_before_tax_match:
            financial_data['税引前当期純利益'] = profit_before_tax_match.group(1).replace(',', '')
        
        profit_match = re.search(r'当期純利益\D+(\d{1,3}(,\d{3})*|\d+)', text)
        if profit_match:
            financial_data['当期純利益'] = profit_match.group(1).replace(',', '')
        
        if len(financial_data) < 5:
            patterns = [
                (r'現金及び預金\s*(\d{1,3}(,\d{3})*|\d+)', '現金及び預金'),
                (r'売掛金\s*(\d{1,3}(,\d{3})*|\d+)', '売掛金等'),
                (r'完成工事未収入金\s*(\d{1,3}(,\d{3})*|\d+)', '売掛金等'),
                (r'たな卸資産\s*(\d{1,3}(,\d{3})*|\d+)', 'たな卸資産'),
                (r'流動資産合計\s*(\d{1,3}(,\d{3})*|\d+)', '流動資産合計'),
                (r'固定資産合計\s*(\d{1,3}(,\d{3})*|\d+)', '固定資産合計'),
                (r'資産合計\s*(\d{1,3}(,\d{3})*|\d+)', '資産合計'),
                (r'買掛金\s*(\d{1,3}(,\d{3})*|\d+)', '買掛金等'),
                (r'工事未払金\s*(\d{1,3}(,\d{3})*|\d+)', '買掛金等'),
                (r'短期借入金\s*(\d{1,3}(,\d{3})*|\d+)', '短期借入金'),
                (r'流動負債合計\s*(\d{1,3}(,\d{3})*|\d+)', '流動負債合計'),
                (r'長期借入金\s*(\d{1,3}(,\d{3})*|\d+)', '長期借入金'),
                (r'固定負債合計\s*(\d{1,3}(,\d{3})*|\d+)', '固定負債合計'),
                (r'負債合計\s*(\d{1,3}(,\d{3})*|\d+)', '負債合計'),
                (r'資本金\s*(\d{1,3}(,\d{3})*|\d+)', '資本金'),
                (r'利益剰余金\s*(\d{1,3}(,\d{3})*|\d+)', '利益剰余金'),
                (r'純資産合計\s*(\d{1,3}(,\d{3})*|\d+)', '純資産合計'),
                (r'売上高\s*(\d{1,3}(,\d{3})*|\d+)', '売上高'),
                (r'完成工事高\s*(\d{1,3}(,\d{3})*|\d+)', '売上高'),
                (r'売上原価\s*(\d{1,3}(,\d{3})*|\d+)', '売上原価'),
                (r'完成工事原価\s*(\d{1,3}(,\d{3})*|\d+)', '売上原価'),
                (r'売上総利益\s*(\d{1,3}(,\d{3})*|\d+)', '売上総利益'),
                (r'販売費及び一般管理費\s*(\d{1,3}(,\d{3})*|\d+)', '販売費及び一般管理費'),
                (r'営業利益\s*(\d{1,3}(,\d{3})*|\d+)', '営業利益'),
                (r'経常利益\s*(\d{1,3}(,\d{3})*|\d+)', '経常利益'),
                (r'税引前当期純利益\s*(\d{1,3}(,\d{3})*|\d+)', '税引前当期純利益'),
                (r'当期純利益\s*(\d{1,3}(,\d{3})*|\d+)', '当期純利益'),
            ]
            
            for pattern, key in patterns:
                match = re.search(pattern, text)
                if match and key not in financial_data:
                    financial_data[key] = match.group(1).replace(',', '')
        
        return financial_data
    
    def create_financial_charts(self):
        """Create financial charts based on the extracted data using the custom visualization format."""
        df = pd.DataFrame(self.financial_data).T
        
        df = df.apply(pd.to_numeric, errors='coerce')
        
        df = df.sort_index()
        
        # Create charts directory
        charts_dir = os.path.join(self.output_dir, "charts")
        os.makedirs(charts_dir, exist_ok=True)
        
        if '売上高' in df.columns and '当期純利益' in df.columns:
            df['売上高利益率'] = df['当期純利益'] / df['売上高'] * 100
        
        if '資産合計' in df.columns and '当期純利益' in df.columns:
            df['ROA'] = df['当期純利益'] / df['資産合計'] * 100
        
        if '純資産合計' in df.columns and '当期純利益' in df.columns:
            df['ROE'] = df['当期純利益'] / df['純資産合計'] * 100
        
        # Create the custom visualization using the FinancialVisualizer
        self.status_label.config(text="サンプルフォーマットに合わせた三期決算図を生成中...")
        
        visualizer = FinancialVisualizer(df, company_name="エピック")
        
        output_path = os.path.join(self.output_dir, "エピック_三期決算図.png")
        fig = visualizer.create_visualization(output_path)
        
        self.save_reference_charts(df, charts_dir)
        
        self.update_preview(fig)
        
        csv_path = os.path.join(self.output_dir, "エピック_財務データ.csv")
        df.to_csv(csv_path)
        
        return df
        
    def save_reference_charts(self, df, charts_dir):
        """Save individual reference charts for documentation purposes."""
        plt.figure(figsize=(10, 6))
        balance_sheet_items = ['資産合計', '負債合計', '純資産合計']
        if all(item in df.columns for item in balance_sheet_items):
            for item in balance_sheet_items:
                plt.plot(df.index, df[item], marker='o', label=item)
            plt.title('貸借対照表の推移')
            plt.xlabel('期')
            plt.ylabel('金額（円）')
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.savefig(os.path.join(charts_dir, 'balance_sheet_chart.png'))
            plt.close()
        
        plt.figure(figsize=(10, 6))
        income_statement_items = ['売上高', '売上総利益', '営業利益', '経常利益', '当期純利益']
        available_items = [item for item in income_statement_items if item in df.columns]
        
        if available_items:
            for item in available_items:
                plt.plot(df.index, df[item], marker='o', label=item)
            plt.title('損益計算書の推移')
            plt.xlabel('期')
            plt.ylabel('金額（円）')
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.savefig(os.path.join(charts_dir, 'income_statement_chart.png'))
            plt.close()
        
        plt.figure(figsize=(10, 6))
        ratio_items = ['売上高利益率', 'ROA', 'ROE']
        available_ratios = [item for item in ratio_items if item in df.columns]
        
        if available_ratios:
            for item in available_ratios:
                plt.plot(df.index, df[item], marker='o', label=item)
            plt.title('財務比率の推移')
            plt.xlabel('期')
            plt.ylabel('比率 (%)')
            plt.legend()
            plt.grid(True, linestyle='--', alpha=0.7)
            plt.savefig(os.path.join(charts_dir, 'financial_ratios_chart.png'))
            plt.close()
    
    def update_preview(self, fig):
        """Update the preview canvas with the given figure."""
        for widget in self.canvas_frame.winfo_children():
            widget.destroy()
        
        canvas = FigureCanvasTkAgg(fig, self.canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

def main():
    root = tk.Tk()
    app = FinancialAnalyzerApp(root)
    root.mainloop()

if __name__ == "__main__":
    main()
