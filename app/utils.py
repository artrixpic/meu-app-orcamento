from decimal import Decimal, ROUND_HALF_UP

def safe_decimal(val):
    try:
        if val is None or val == '': return Decimal('0.00')
        val = str(val).replace(',', '.')
        return Decimal(val).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
    except:
        return Decimal('0.00')

def safe_int(val, default=0):
    try: return int(float(val))
    except: return default