from datetime import datetime


class URLGenerator:
    """
    Generates AMFI Excel download URLs based on current month and year.
    URL pattern: https://portal.amfiindia.com/spages/am{month}{year}repo.xls
    """
    
    BASE_URL = "https://portal.amfiindia.com/spages/am{month}{year}repo.xls"
    
    # Month mapping: number to short form
    MONTH_MAP = {
        1: 'jan',
        2: 'feb',
        3: 'mar',
        4: 'apr',
        5: 'may',
        6: 'jun',
        7: 'jul',
        8: 'aug',
        9: 'sep',
        10: 'oct',
        11: 'nov',
        12: 'dec'
    }
    
    @classmethod
    def generate_current_month_url(cls):
        """
        Generate URL for the current month.
        
        Returns:
            dict: {
                'url': str,
                'month': str,  # e.g., 'jan'
                'year': int    # e.g., 2025
            }
        """
        now = datetime.now()
        current_month_number = now.month
        current_year = now.year
        
        month_short = cls.MONTH_MAP[current_month_number]
        
        url = cls.BASE_URL.format(
            month=month_short,
            year=current_year
        )
        
        return {
            'url': url,
            'month': month_short,
            'year': current_year
        }
    
    @classmethod
    def generate_url_for_date(cls, month, year):
        """
        Generate URL for a specific month and year.
        
        Args:
            month (str): Month in short form (e.g., 'jan', 'feb')
            year (int): 4-digit year (e.g., 2025)
        
        Returns:
            str: Generated URL
        """
        url = cls.BASE_URL.format(
            month=month.lower(),
            year=year
        )
        return url