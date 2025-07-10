import re
from datetime import date, timedelta
import os
import argparse
import sys

class OIAnalyzer:
    """
    Analyzes financial market data for abnormal Open Interest (OI) situations.
    
    Abnormal situation definition:
    - OI Ratio >= 2.0 (one value is at least double the other)
    - NEAR Ratio <= 1.2 (values are balanced within 20%)
    - TOTAL Ratio <= 1.2 (values are balanced within 20%)
    """
    
    def __init__(self, base_path=None, oi_threshold=2.0, balance_threshold=1.2):
        """
        Initialize the OI analyzer with configurable parameters.
        
        Args:
            base_path (str): Base directory path for data files
            oi_threshold (float): Minimum OI ratio to consider imbalanced
            balance_threshold (float): Maximum ratio to consider balanced
        """
        self.base_path = base_path or "/storage/emulated/0/Download/Telegram/Kite_Zerodha/Textfiles/"
        self.oi_threshold = oi_threshold
        self.balance_threshold = balance_threshold
        
        # Regex pattern to match the data format
        self.pattern = re.compile(r"""
            \*{8}\s+([\d-]+\s+\d{2}:\d{2}:\d{2})\s+\*{8}.*?  # Capture timestamp
            CE\s+\[\s*([\d.-]+)\s*\]\s+OI\s+PE\s+\[\s*([\d.-]+)\s*\].*?  # Capture OI values
            CE\s+\[\s*([\d.-]+)\s*\]\s+NEAR\s+PE\s+\[\s*([\d.-]+)\s*\].*?  # Capture NEAR values
            CE\s+\[\s*([\d.-]+)\s*\]\s+TOTAL\s+PE\s+\[\s*([\d.-]+)\s*\]  # Capture TOTAL values
            """, re.DOTALL | re.VERBOSE)

    def parse_data_block(self, match):
        """
        Parse a single data block match and return structured data.
        
        Args:
            match: Regex match object
            
        Returns:
            dict: Parsed data or None if parsing fails
        """
        try:
            return {
                'timestamp': match.group(1),
                'ce_oi': float(match.group(2)),
                'pe_oi': float(match.group(3)),
                'ce_near': float(match.group(4)),
                'pe_near': float(match.group(5)),
                'ce_total': float(match.group(6)),
                'pe_total': float(match.group(7))
            }
        except (ValueError, IndexError) as e:
            print(f"    Error parsing data: {e}")
            return None

    def calculate_ratios(self, data):
        """
        Calculate CE/PE ratios for OI, NEAR, and TOTAL values.
        
        Args:
            data (dict): Parsed data dictionary
            
        Returns:
            dict: Calculated ratios or None if any value is zero
        """
        values = [data['ce_oi'], data['pe_oi'], data['ce_near'], 
                 data['pe_near'], data['ce_total'], data['pe_total']]
        
        # Skip if any value is zero to avoid ZeroDivisionError
        if 0 in values:
            return None
            
        return {
            'oi_ratio': max(data['ce_oi'], data['pe_oi']) / min(data['ce_oi'], data['pe_oi']),
            'near_ratio': max(data['ce_near'], data['pe_near']) / min(data['ce_near'], data['pe_near']),
            'total_ratio': max(data['ce_total'], data['pe_total']) / min(data['ce_total'], data['pe_total'])
        }

    def is_abnormal_condition(self, ratios):
        """
        Check if the calculated ratios meet the abnormal condition criteria.
        
        Args:
            ratios (dict): Dictionary with calculated ratios
            
        Returns:
            bool: True if abnormal condition detected
        """
        return (ratios['oi_ratio'] >= self.oi_threshold and 
                ratios['near_ratio'] <= self.balance_threshold and 
                ratios['total_ratio'] <= self.balance_threshold)

    def analyze_content(self, content, source=""):
        """
        Analyze content for abnormal OI situations.
        
        Args:
            content (str): Text content to analyze
            source (str): Source identifier for logging
            
        Returns:
            list: List of abnormal conditions found
        """
        abnormal_conditions = []
        matches = self.pattern.finditer(content)
        
        for match in matches:
            data = self.parse_data_block(match)
            if not data:
                continue
                
            ratios = self.calculate_ratios(data)
            if not ratios:
                continue
                
            if self.is_abnormal_condition(ratios):
                result = {
                    'source': source,
                    'data': data,
                    'ratios': ratios
                }
                abnormal_conditions.append(result)
                
        return abnormal_conditions

    def print_abnormal_condition(self, condition):
        """Print formatted abnormal condition details."""
        data = condition['data']
        ratios = condition['ratios']
        
        print("\n--- Found Abnormal Condition! ---")
        print(f"    Source: {condition['source']}")
        print(f"    Date & Time: {data['timestamp']}")
        print(f"    OI:    CE = {data['ce_oi']}, PE = {data['pe_oi']} (Ratio: {ratios['oi_ratio']:.2f})")
        print(f"    NEAR:  CE = {data['ce_near']}, PE = {data['pe_near']} (Ratio: {ratios['near_ratio']:.2f})")
        print(f"    TOTAL: CE = {data['ce_total']}, PE = {data['pe_total']} (Ratio: {ratios['total_ratio']:.2f})")
        print("---------------------------------")

    def analyze_files(self, stock_name, days_to_check):
        """
        Analyze files for a specific stock over a given number of days.
        
        Args:
            stock_name (str): Stock name (e.g., 'SENSEX')
            days_to_check (int): Number of past days to check
            
        Returns:
            list: All abnormal conditions found
        """
        stock_name_upper = stock_name.upper()
        print(f"\nStarting analysis for: {stock_name_upper} for the last {days_to_check} days...")
        print(f"Base path: {self.base_path}")
        
        all_abnormal_conditions = []
        files_checked = 0
        
        for i in range(days_to_check):
            current_date = date.today() - timedelta(days=i)
            date_str = current_date.strftime("%Y-%m-%d")
            
            file_path = os.path.join(self.base_path, stock_name_upper, f"{stock_name_upper}-{date_str}.txt")
            
            if not os.path.exists(file_path):
                continue
                
            files_checked += 1
            print(f"Scanning file: {file_path}")
            
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                conditions = self.analyze_content(content, f"{stock_name_upper}-{date_str}.txt")
                all_abnormal_conditions.extend(conditions)
                
                for condition in conditions:
                    self.print_abnormal_condition(condition)
                    
            except Exception as e:
                print(f"    Error reading file {file_path}: {e}")
                
        print(f"\nScan complete. Checked {files_checked} files.")
        if not all_abnormal_conditions:
            print("No abnormal situations were found in the available files.")
        else:
            print(f"Found {len(all_abnormal_conditions)} abnormal conditions.")
            
        return all_abnormal_conditions

    def analyze_sample_data(self, sample_data, verbose=True):
        """
        Analyze sample data for testing purposes.
        
        Args:
            sample_data (str): Sample data string
            verbose (bool): Whether to print detailed output
            
        Returns:
            list: All conditions found (both normal and abnormal)
        """
        if verbose:
            print("\n=== Analyzing Sample Data ===")
        
        all_conditions = []
        matches = self.pattern.finditer(sample_data)
        
        for match in matches:
            data = self.parse_data_block(match)
            if not data:
                continue
                
            ratios = self.calculate_ratios(data)
            if not ratios:
                continue
                
            condition = {
                'source': 'sample_data',
                'data': data,
                'ratios': ratios,
                'is_abnormal': self.is_abnormal_condition(ratios)
            }
            all_conditions.append(condition)
            
            if verbose:
                print(f"\nTimestamp: {data['timestamp']}")
                print(f"OI:    CE = {data['ce_oi']:8.2f}, PE = {data['pe_oi']:8.2f} (Ratio: {ratios['oi_ratio']:.2f})")
                print(f"NEAR:  CE = {data['ce_near']:8.2f}, PE = {data['pe_near']:8.2f} (Ratio: {ratios['near_ratio']:.2f})")
                print(f"TOTAL: CE = {data['ce_total']:8.2f}, PE = {data['pe_total']:8.2f} (Ratio: {ratios['total_ratio']:.2f})")
                
                if condition['is_abnormal']:
                    print("*** ABNORMAL CONDITION DETECTED! ***")
                else:
                    print("Normal condition")
        
        if verbose:
            abnormal_count = sum(1 for c in all_conditions if c['is_abnormal'])
            print(f"\nTotal data blocks found: {len(all_conditions)}")
            print(f"Abnormal conditions: {abnormal_count}")
        
        return all_conditions


def main():
    """Main function to handle command line usage."""
    parser = argparse.ArgumentParser(description='Analyze financial market data for abnormal OI situations')
    parser.add_argument('--stock', type=str, help='Stock name to analyze')
    parser.add_argument('--days', type=int, default=20, help='Number of days to check (default: 20)')
    parser.add_argument('--path', type=str, help='Base path for data files')
    parser.add_argument('--test', action='store_true', help='Run with sample data for testing')
    parser.add_argument('--oi-threshold', type=float, default=2.0, help='OI imbalance threshold (default: 2.0)')
    parser.add_argument('--balance-threshold', type=float, default=1.2, help='Balance threshold (default: 1.2)')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = OIAnalyzer(
        base_path=args.path,
        oi_threshold=args.oi_threshold,
        balance_threshold=args.balance_threshold
    )
    
    if args.test:
        # Test with sample data
        sample_data = """
******** 08-07-2025 14:55:17 *********
Price: 83538.22
Total PCR: 0.9           PCR: 0.97
High: 83566.77            Low: 83320.95
**************************************
CE [ 1044.16 ]    OI     PE [ 1139.31 ]
CE [ 1171.78 ]   NEAR    PE [ 1218.66 ]
CE [ 1872.26 ]   TOTAL   PE [ 1819.52 ]
**************************************

******** 08-07-2025 15:29:40 *********
Price: 83720.86
Total PCR: 1.05           PCR: 1.32
High: 83812.31            Low: 83320.95
**************************************
CE [  633.8 ]    OI     PE [ 876.35 ]
CE [ 703.12 ]   NEAR    PE [ 951.62 ]
CE [ 1052.79 ]   TOTAL   PE [ 1394.09 ]
**************************************
"""
        analyzer.analyze_sample_data(sample_data)
        
    elif args.stock:
        # Analyze files for specific stock
        analyzer.analyze_files(args.stock, args.days)
        
    else:
        # Interactive mode (for backward compatibility)
        print("OI Analyzer - Interactive Mode")
        print("1. Test with sample data")
        print("2. Analyze files (requires data directory)")
        
        try:
            choice = input("\nChoose option (1 or 2): ")
            
            if choice == "1":
                sample_data = """
******** 08-07-2025 14:55:17 *********
Price: 83538.22
Total PCR: 0.9           PCR: 0.97
High: 83566.77            Low: 83320.95
**************************************
CE [ 1044.16 ]    OI     PE [ 1139.31 ]
CE [ 1171.78 ]   NEAR    PE [ 1218.66 ]
CE [ 1872.26 ]   TOTAL   PE [ 1819.52 ]
**************************************

******** 08-07-2025 15:29:40 *********
Price: 83720.86
Total PCR: 1.05           PCR: 1.32
High: 83812.31            Low: 83320.95
**************************************
CE [  633.8 ]    OI     PE [ 876.35 ]
CE [ 703.12 ]   NEAR    PE [ 951.62 ]
CE [ 1052.79 ]   TOTAL   PE [ 1394.09 ]
**************************************
"""
                analyzer.analyze_sample_data(sample_data)
                
            elif choice == "2":
                stock_name = input("Enter stock name (e.g., SENSEX): ")
                days = int(input("Number of days to check (e.g., 20): "))
                analyzer.analyze_files(stock_name, days)
                
            else:
                print("Invalid choice.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()