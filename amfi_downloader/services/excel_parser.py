import pandas as pd
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class ExcelParser:
    """
    Parses AMFI Excel files to extract Growth/Equity Oriented Scheme data.
    Handles various Excel formats and edge cases.
    """
    
    # Keywords to identify the Growth/Equity section
    START_KEYWORDS = ["growth", "equity", "oriented"]
    END_KEYWORDS = ["sub total", "subtotal", "sub-total"]
    HEADER_KEYWORDS = ["scheme", "net", "assets", "aum", "rs.", "₹"]
    
    # Scheme categories mapping (for standardization)
    SCHEME_MAPPING = {
        "multi cap fund": "MULTI CAP FUND",
        "large cap fund": "LARGE CAP FUND",
        "large & mid cap fund": "LARGE & MID CAP FUND",
        "mid cap fund": "MID CAP FUND",
        "small cap fund": "SMALL CAP FUND",
        "dividend yield fund": "DIVIDEND YIELD FUND",
        "value fund/contra fund": "VALUE FUND/CONTRA FUND",
        "focused fund": "FOCUSED FUND",
        "sectoral/thematic": "SECTORAL/THEMATIC FUNDS",
        "elss": "ELSS",
        "flexi cap fund": "FLEXI CAP FUND",
    }
    
    @classmethod
    def parse_excel(cls, file_path, month, year):
        """
        Parse Excel file and extract Growth/Equity section data.
        
        Args:
            file_path (str): Path to Excel file
            month (str): Month in short form (e.g., 'jan')
            year (int): Year (e.g., 2025)
        
        Returns:
            list of dict: Parsed data in format:
                [
                    {'month': '01-Oct-25', 'scheme': 'Small Cap Fund', 'net_inflow': 3476.04},
                    {'month': '01-Oct-25', 'scheme': 'Large Cap Fund', 'net_inflow': 971.97},
                ]
            Returns empty list if parsing fails.
        """
        try:
            # Read Excel file
            df_raw = pd.read_excel(file_path, header=None)
            df_raw = df_raw.astype(str)
            
            # Find header row
            header_row = cls._find_header_row(df_raw)
            if header_row is None:
                logger.warning(f"Could not find header row in {file_path}")
                return []
            
            # Set header and clean dataframe
            df = df_raw.copy()
            df.columns = df.iloc[header_row]
            df = df.iloc[header_row + 1:].reset_index(drop=True)
            df = df.loc[:, df.columns.notna()]
            df_str = df.astype(str)
            
            # Find Growth/Equity section
            start_idx, end_idx = cls._find_growth_equity_section(df_str)
            if start_idx is None or end_idx is None:
                logger.warning(f"Could not find Growth/Equity section in {file_path}")
                return []
            
            # Extract section
            section_df = df.iloc[start_idx:end_idx].copy()
            section_df = section_df.dropna(how='all').reset_index(drop=True)
            
            # Parse data
            parsed_data = cls._parse_section_data(section_df, month, year)
            
            logger.info(f"Successfully parsed {len(parsed_data)} schemes from {file_path}")
            return parsed_data
        
        except Exception as e:
            logger.error(f"Error parsing {file_path}: {str(e)}")
            return []
    
    @classmethod
    def _find_header_row(cls, df):
        """
        Find the row containing column headers.
        """
        for i, row in df.iterrows():
            row_text = " ".join(row).lower()
            if any(keyword in row_text for keyword in cls.HEADER_KEYWORDS):
                return i
        return None
    
    @classmethod
    def _find_growth_equity_section(cls, df):
        """
        Find start and end indices of Growth/Equity Oriented Scheme section.
        """
        start_idx = None
        end_idx = None
        
        # Find start
        for i, row in df.iterrows():
            row_text = " ".join(row).lower()
            if all(keyword in row_text for keyword in cls.START_KEYWORDS):
                start_idx = i
                break
        
        # Find end (from start point)
        if start_idx is not None:
            for i in range(start_idx + 1, len(df)):
                row_text = " ".join(df.iloc[i]).lower()
                if any(keyword in row_text for keyword in cls.END_KEYWORDS):
                    end_idx = i
                    break
        
        return start_idx, end_idx
    
    @classmethod
    def _parse_section_data(cls, section_df, month, year):
        """
        Parse the extracted section into structured data.
        """
        parsed_data = []
        month_label = cls._format_month_label(month, year)
        
        for _, row in section_df.iterrows():
            # Scheme name is typically in column 1 (index 1)
            scheme_raw = str(row.iloc[1]).strip() if len(row) > 1 else ""
            
            # Net inflow is typically in column 6 (index 6)
            net_inflow_raw = row.iloc[6] if len(row) > 6 else None
            
            # Skip invalid rows
            if not scheme_raw or cls._is_invalid_row(scheme_raw):
                continue
            
            # Parse net inflow
            try:
                net_inflow = float(net_inflow_raw)
            except (ValueError, TypeError):
                continue
            
            # Standardize scheme name
            scheme_standardized = cls._standardize_scheme_name(scheme_raw)
            
            parsed_data.append({
                'month': month_label,
                'scheme': scheme_standardized,
                'net_inflow': net_inflow
            })
        
        return parsed_data
    
    @classmethod
    def _is_invalid_row(cls, scheme_text):
        """
        Check if row should be skipped.
        """
        scheme_lower = scheme_text.lower()
        invalid_keywords = [
            "sub total",
            "subtotal",
            "sub-total",
            "growth/equity",
            "oriented scheme",
        ]
        return any(keyword in scheme_lower for keyword in invalid_keywords)
    
    @classmethod
    def _standardize_scheme_name(cls, scheme_raw):
        """
        Standardize scheme names to match dashboard format.
        """
        scheme_lower = scheme_raw.lower().strip()
        
        # Check mapping
        for key, standardized in cls.SCHEME_MAPPING.items():
            if key in scheme_lower:
                return standardized
        
        # If no match, return title case
        return scheme_raw.strip().title()
    
    @classmethod
    def _format_month_label(cls, month, year):
        """
        Format month label as "01-Oct-25" style.
        
        Args:
            month (str): Short month name (e.g., 'oct')
            year (int): Full year (e.g., 2025)
        
        Returns:
            str: Formatted label (e.g., '01-Oct-25')
        """
        # Month name mapping
        month_names = {
            'jan': 'Jan', 'feb': 'Feb', 'mar': 'Mar', 'apr': 'Apr',
            'may': 'May', 'jun': 'Jun', 'jul': 'Jul', 'aug': 'Aug',
            'sep': 'Sep', 'oct': 'Oct', 'nov': 'Nov', 'dec': 'Dec'
        }
        
        month_abbr = month_names.get(month.lower(), month.title())
        year_short = str(year)[-2:]  # Last 2 digits of year
        
        return f"01-{month_abbr}-{year_short}"