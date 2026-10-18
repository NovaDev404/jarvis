import re
from fractions import Fraction
import math

def calculate(expression, output_format="decimal"):
    """
    Evaluate a mathematical expression following BEDMAS/BODMAS order of operations.
    
    Args:
        expression: Mathematical expression as string (e.g., "3 + (4*7 / 3^2)")
        output_format: One of "decimal" or "fraction"
    
    Returns:
        Result as string in the requested format
    """
    try:
        # Replace common mathematical symbols with Python equivalents
        # Handle caret (^) for exponentiation
        expr = expression.replace("^", "**")
        
        # Evaluate the expression safely
        result = eval(expr, {"__builtins__": {}}, {"math": math})
        
        # Format the result based on requested output format
        if output_format == "decimal":
            # Return with appropriate precision
            if isinstance(result, float):
                if result.is_integer():
                    return str(int(result))
                else:
                    return str(round(result, 10))
            return str(result)
        elif output_format == "fraction":
            # Convert to fraction
            if isinstance(result, float):
                frac = Fraction(result).limit_denominator(1000)
                return f"{frac.numerator}/{frac.denominator}"
            else:
                return f"{result}/1"
        else:
            return str(float(result))
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error: {str(e)}"

tool = {
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "Evaluate mathematical expressions following BEDMAS/BODMAS order of operations (Brackets, Exponents, Division/Multiplication, Addition/Subtraction). Supports ^ for exponents.",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "Mathematical expression to evaluate (e.g., '3 + (4*7 / 3^2)')"
                },
                "output_format": {
                    "type": "string",
                    "description": "Output format: 'decimal' (default) or 'fraction'",
                    "enum": ["decimal", "fraction"]
                }
            },
            "required": ["expression"]
        },
        "implementation": calculate
    },
    "critical": False
}
