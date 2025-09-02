"""
A simple calculator class demonstrating basic arithmetic operations.
This fixture provides examples of classes, methods, and documentation.
"""

import math
from typing import Union


class Calculator:
    """A basic calculator with arithmetic operations and memory functionality."""
    
    def __init__(self):
        """Initialize calculator with zero memory."""
        self.memory = 0.0
        self.history = []
    
    def add(self, a: float, b: float) -> float:
        """Add two numbers and return the result."""
        result = a + b
        self.history.append(f"add({a}, {b}) = {result}")
        return result
    
    def subtract(self, a: float, b: float) -> float:
        """Subtract b from a and return the result."""
        result = a - b
        self.history.append(f"subtract({a}, {b}) = {result}")
        return result
    
    def multiply(self, a: float, b: float) -> float:
        """Multiply two numbers and return the result."""
        result = a * b
        self.history.append(f"multiply({a}, {b}) = {result}")
        return result
    
    def divide(self, a: float, b: float) -> float:
        """Divide a by b and return the result. Raises ValueError if b is zero."""
        if b == 0:
            raise ValueError("Cannot divide by zero")
        result = a / b
        self.history.append(f"divide({a}, {b}) = {result}")
        return result
    
    def power(self, base: float, exponent: float) -> float:
        """Calculate base raised to the power of exponent."""
        result = math.pow(base, exponent)
        self.history.append(f"power({base}, {exponent}) = {result}")
        return result
    
    def square_root(self, number: float) -> float:
        """Calculate the square root of a number."""
        if number < 0:
            raise ValueError("Cannot calculate square root of negative number")
        result = math.sqrt(number)
        self.history.append(f"sqrt({number}) = {result}")
        return result
    
    def store_memory(self, value: float) -> None:
        """Store a value in calculator memory."""
        self.memory = value
    
    def recall_memory(self) -> float:
        """Recall the value stored in calculator memory."""
        return self.memory
    
    def clear_memory(self) -> None:
        """Clear the calculator memory."""
        self.memory = 0.0
    
    def clear_history(self) -> None:
        """Clear the calculation history."""
        self.history = []
    
    def get_history(self) -> list:
        """Get the calculation history."""
        return self.history.copy()


def calculate_compound_interest(principal: float, rate: float, time: float, compounds_per_year: int = 1) -> float:
    """
    Calculate compound interest using the formula A = P(1 + r/n)^(nt).
    
    Args:
        principal: Initial amount of money
        rate: Annual interest rate (as decimal)
        time: Time in years
        compounds_per_year: Number of times interest compounds per year
    
    Returns:
        Final amount after compound interest
    """
    if principal < 0 or rate < 0 or time < 0:
        raise ValueError("Principal, rate, and time must be non-negative")
    
    amount = principal * (1 + rate / compounds_per_year) ** (compounds_per_year * time)
    return round(amount, 2)


# Global constants for mathematical operations
PI = math.pi
E = math.e
GOLDEN_RATIO = (1 + math.sqrt(5)) / 2