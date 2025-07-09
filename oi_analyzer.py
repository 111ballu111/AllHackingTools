import re
from datetime import date, timedelta
import os

def find_abnormal_oi_situation(stock_name, days_to_check):
    """
    This function scans data files for a specific abnormal OI situation and prints the findings.
    
    Abnormal situation definition:
    - OI Ratio >= 2.0 (one value is at least double the other)
    - NEAR Ratio <= 1.2 (values are balanced within 20%)
    - TOTAL Ratio <= 1.2 (values are balanced within 20%)
    """
    
    # Convert stock name to uppercase to handle case-insensitivity
    stock_name_upper = stock_name.upper()
    
    print(f"\nStarting automatic analysis for: {stock_name_upper} for the last {days_to_check} days...")
    
    # --- Internal Thresholds ---
    OI_IMBALANCE_THRESHOLD = 2.0
    NEAR_TOTAL_BALANCE_THRESHOLD = 1.2
    
    base_path = "/storage/emulated/0/Download/Telegram/Kite_Zerodha/Textfiles/"
    found_any_match = False

    # Loop through the last 'n' days
    for i in range(days_to_check):
        current_date = date.today() - timedelta(days=i)
        date_str = current_date.strftime("%Y-%m-%d")
        
        file_path = os.path.join(base_path, stock_name_upper, f"{stock_name_upper}-{date_str}.txt")

        if not os.path.exists(file_path):
            continue
            
        #print(f"\n--> Scanning file: {file_path}")

        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"    Error: Could not read file {file_path}. Error: {e}")
            continue
        
        # Fixed regex pattern to match the actual data format
        pattern = re.compile(r"""
            \*{8}\s+([\d-]+\s+\d{2}:\d{2}:\d{2})\s+\*{8}.*?  # Capture timestamp
            CE\s+\[\s*([\d.-]+)\s*\]\s+OI\s+PE\s+\[\s*([\d.-]+)\s*\].*?  # Capture OI values
            CE\s+\[\s*([\d.-]+)\s*\]\s+NEAR\s+PE\s+\[\s*([\d.-]+)\s*\].*?  # Capture NEAR values
            CE\s+\[\s*([\d.-]+)\s*\]\s+TOTAL\s+PE\s+\[\s*([\d.-]+)\s*\]  # Capture TOTAL values
            """, re.DOTALL | re.VERBOSE)

        matches = pattern.finditer(content)
        
        for match in matches:
            try:
                timestamp = match.group(1)
                ce_oi = float(match.group(2))
                pe_oi = float(match.group(3))
                ce_near = float(match.group(4))
                pe_near = float(match.group(5))
                ce_total = float(match.group(6))
                pe_total = float(match.group(7))
            except (ValueError, IndexError) as e:
                print(f"    Error parsing data: {e}")
                continue

            # Skip if any value is zero to avoid ZeroDivisionError and meaningless ratios
            if 0 in [ce_oi, pe_oi, ce_near, pe_near, ce_total, pe_total]:
                continue

            # Calculate ratios (always >= 1 for easier comparison)
            oi_ratio = max(ce_oi, pe_oi) / min(ce_oi, pe_oi)
            near_ratio = max(ce_near, pe_near) / min(ce_near, pe_near)
            total_ratio = max(ce_total, pe_total) / min(ce_total, pe_total)

            # Check the conditions
            if (oi_ratio >= OI_IMBALANCE_THRESHOLD and 
                near_ratio <= NEAR_TOTAL_BALANCE_THRESHOLD and 
                total_ratio <= NEAR_TOTAL_BALANCE_THRESHOLD):
                
                found_any_match = True
                print("\n--- Found Abnormal Condition! ---")
                print(f"    Date & Time: {timestamp}")
                print(f"    OI:    CE = {ce_oi}, PE = {pe_oi} (Ratio: {oi_ratio:.2f})")
                print(f"    NEAR:  CE = {ce_near}, PE = {pe_near} (Ratio: {near_ratio:.2f})")
                print(f"    TOTAL: CE = {ce_total}, PE = {pe_total} (Ratio: {total_ratio:.2f})")
                print("---------------------------------")

    if not found_any_match:
        print("\nAnalysis complete. No abnormal situations were found in the available files.")


def analyze_sample_data(sample_data):
    """
    Analyze the sample data provided to test the regex pattern
    """
    print("\n=== Analyzing Sample Data ===")
    
    # Improved regex pattern for the sample data format
    pattern = re.compile(r"""
        \*{8}\s+([\d-]+\s+\d{2}:\d{2}:\d{2})\s+\*{8}.*?  # Capture timestamp
        CE\s+\[\s*([\d.-]+)\s*\]\s+OI\s+PE\s+\[\s*([\d.-]+)\s*\].*?  # Capture OI values
        CE\s+\[\s*([\d.-]+)\s*\]\s+NEAR\s+PE\s+\[\s*([\d.-]+)\s*\].*?  # Capture NEAR values
        CE\s+\[\s*([\d.-]+)\s*\]\s+TOTAL\s+PE\s+\[\s*([\d.-]+)\s*\]  # Capture TOTAL values
        """, re.DOTALL | re.VERBOSE)

    matches = pattern.finditer(sample_data)
    
    OI_IMBALANCE_THRESHOLD = 2.0
    NEAR_TOTAL_BALANCE_THRESHOLD = 1.2
    found_matches = 0
    
    for match in matches:
        try:
            timestamp = match.group(1)
            ce_oi = float(match.group(2))
            pe_oi = float(match.group(3))
            ce_near = float(match.group(4))
            pe_near = float(match.group(5))
            ce_total = float(match.group(6))
            pe_total = float(match.group(7))
            
            found_matches += 1
            
            # Skip if any value is zero
            if 0 in [ce_oi, pe_oi, ce_near, pe_near, ce_total, pe_total]:
                continue

            # Calculate ratios
            oi_ratio = max(ce_oi, pe_oi) / min(ce_oi, pe_oi)
            near_ratio = max(ce_near, pe_near) / min(ce_near, pe_near)
            total_ratio = max(ce_total, pe_total) / min(ce_total, pe_total)

            print(f"\nTimestamp: {timestamp}")
            print(f"OI:    CE = {ce_oi:8.2f}, PE = {pe_oi:8.2f} (Ratio: {oi_ratio:.2f})")
            print(f"NEAR:  CE = {ce_near:8.2f}, PE = {pe_near:8.2f} (Ratio: {near_ratio:.2f})")
            print(f"TOTAL: CE = {ce_total:8.2f}, PE = {pe_total:8.2f} (Ratio: {total_ratio:.2f})")
            
            # Check abnormal conditions
            if (oi_ratio >= OI_IMBALANCE_THRESHOLD and 
                near_ratio <= NEAR_TOTAL_BALANCE_THRESHOLD and 
                total_ratio <= NEAR_TOTAL_BALANCE_THRESHOLD):
                print("*** ABNORMAL CONDITION DETECTED! ***")
            else:
                print("Normal condition")
                
        except (ValueError, IndexError) as e:
            print(f"Error parsing match: {e}")
    
    print(f"\nTotal matches found: {found_matches}")


# --- How to use the function ---
if __name__ == "__main__":
    # Test with sample data first
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
"""
    
    analyze_sample_data(sample_data)
    
    # Interactive mode
    try:
        
        choice = input("\nChoose option:\n1. Analyze files\n2. Test with sample data\nEnter choice (1 or 2): ")
        
        if choice == "1":
            stock_name_input = input("Enter the stock name (e.g., SENSEX): ")
            days_input = int(input("How many past days to check? (e.g., 20): "))
            find_abnormal_oi_situation(stock_name_input, days_input)
        
        elif choice == "2":
            # Use the provided sample data
            full_sample = """
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
            analyze_sample_data(full_sample)
        
        else:
            print("Invalid choice.")

    except ValueError:
        print("\nInvalid input. Please enter a number for days.")
    except Exception as e:
        print(f"\nAn error occurred: {e}")