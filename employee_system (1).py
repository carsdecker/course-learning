import functools
from typing import List, Dict, Union
from datetime import datetime


# Custom Exception Classes
class InvalidEmployeeDataError(ValueError):
    """Custom exception for invalid employee data."""
    pass


class InvalidHoursError(ValueError):
    """Custom exception for invalid hours worked."""
    pass


# Decorator Functions
def log_employee_action(func):
    """
    Decorator that logs employee-related actions with timestamps.

    Args:
        func: The function to be decorated

    Returns:
        The wrapped function with logging capabilities
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Get current timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # args[0] is "self" (the employee the method was called on)
        employee = args[0] if args else None
        if isinstance(employee, Employee):
            who = f" for {employee.name} ({employee.employee_id})"
        else:
            who = ""

        # Log BEFORE running the real method
        print(f"[{timestamp}] Calling {func.__name__}{who}")

        # Run the real method (if it raises an error, the error passes straight through)
        result = func(*args, **kwargs)

        # Log AFTER the real method finishes
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if result is None:
            print(f"[{timestamp}] {func.__name__} completed")
        else:
            print(f"[{timestamp}] {func.__name__} completed with result: {result}")

        return result

    return wrapper


def validate_positive_hours(func):
    """
    Decorator that validates hours worked are positive and reasonable.

    Args:
        func: The function to be decorated

    Returns:
        The wrapped function with hours validation

    Raises:
        InvalidHoursError: If hours are negative or exceed 168 (hours in a week)
    """

    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # hours_worked is either the 2nd positional argument (after self)
        # or passed by name, e.g. calculate_pay(hours_worked=40)
        if len(args) > 1:
            hours = args[1]
        else:
            hours = kwargs.get("hours_worked")

        if not isinstance(hours, (int, float)):
            raise InvalidHoursError(f"Hours must be a number, got {hours!r}")
        if hours < 0:
            raise InvalidHoursError(f"Hours cannot be negative, got {hours}")
        if hours > 168:
            raise InvalidHoursError(f"Hours cannot exceed 168 per week, got {hours}")

        # Checks passed, so run the real method
        return func(*args, **kwargs)

    return wrapper


# Base Employee Class
class Employee:
    """
    Base class representing an employee with basic information and functionality.

    This class demonstrates static methods, properties, magic methods, and
    serves as the base for inheritance.
    """

    # Class variable to store all employees
    _all_employees: List['Employee'] = []

    def __init__(self, name: str, employee_id: str, hourly_rate: float):
        """
        Initialize an Employee object.

        Args:
            name (str): The employee's full name
            employee_id (str): Unique employee identifier
            hourly_rate (float): Hourly wage rate

        Raises:
            InvalidEmployeeDataError: If any data is invalid
        """
        self.name = name
        self.employee_id = self.validate_employee_id(employee_id)
        self.hourly_rate = self.validate_hourly_rate(hourly_rate)
        self._performance_score = 0.0
        self._reviews = []

        # Add to company employee list
        Employee._all_employees.append(self)

    @staticmethod
    def validate_hourly_rate(rate: float) -> float:
        """
        Validates that the hourly rate is positive and reasonable.

        Args:
            rate (float): The hourly rate to validate

        Returns:
            float: The validated hourly rate

        Raises:
            InvalidEmployeeDataError: If rate is not positive or exceeds $500/hour
        """
        if not isinstance(rate, (int, float)):
            raise InvalidEmployeeDataError(f"Hourly rate must be a number, got {rate!r}")
        if rate <= 0:
            raise InvalidEmployeeDataError(f"Hourly rate must be positive, got {rate}")
        if rate >= 500:
            raise InvalidEmployeeDataError(f"Hourly rate must be under $500/hour, got {rate}")
        return rate

    @staticmethod
    def validate_employee_id(emp_id: str) -> str:
        """
        Validates employee ID format (letters followed by numbers).

        Args:
            emp_id (str): The employee ID to validate

        Returns:
            str: The validated employee ID

        Raises:
            InvalidEmployeeDataError: If ID format is invalid
        """
        if not isinstance(emp_id, str) or not emp_id:
            raise InvalidEmployeeDataError("Employee ID must be a non-empty string")

        # Walk from the front, counting letters
        i = 0
        while i < len(emp_id) and emp_id[i].isalpha():
            i += 1

        letters = emp_id[:i]   # "EMP001" -> "EMP"
        digits = emp_id[i:]    # "EMP001" -> "001"

        if not (letters.isalpha() and digits.isdigit()):
            raise InvalidEmployeeDataError(
                f"Employee ID must start with letters and end with numbers, got '{emp_id}'"
            )
        return emp_id

    @log_employee_action
    @validate_positive_hours
    def calculate_pay(self, hours_worked: float) -> float:
        """
        Calculate basic pay for hours worked.

        Args:
            hours_worked (float): Number of hours worked

        Returns:
            float: Total pay amount
        """
        return self.hourly_rate * hours_worked

    @log_employee_action
    def calculate_benefits(self, hours_worked: float) -> float:
        """
        Calculate benefits for base employee (default: no benefits).

        Args:
            hours_worked (float): Hours worked this period

        Returns:
            float: Benefits amount
        """
        return 0.0

    @property
    def annual_salary_estimate(self) -> float:
        """
        Estimate annual salary based on 40 hours/week for 52 weeks.

        Returns:
            float: Estimated annual salary
        """
        return self.hourly_rate * 40 * 52

    @property
    def performance_score(self) -> float:
        """
        Get current performance score (average of all reviews).

        Returns:
            float: Current performance score (0-100)
        """
        return self._performance_score

    @log_employee_action
    def add_performance_review(self, score: float, notes: str = "") -> None:
        """
        Add a performance review and update performance score.

        Args:
            score (float): Performance score (0-100)
            notes (str): Review notes

        Raises:
            InvalidEmployeeDataError: If score is not between 0-100
        """
        if not isinstance(score, (int, float)) or not 0 <= score <= 100:
            raise InvalidEmployeeDataError(f"Score must be between 0 and 100, got {score}")

        self._reviews.append({
            "score": score,
            "notes": notes,
            "date": datetime.now().strftime("%Y-%m-%d"),
        })

        # New score = average of every review so far
        total = sum(review["score"] for review in self._reviews)
        self._performance_score = total / len(self._reviews)

    def get_promotion_eligibility(self) -> bool:
        """
        Check if employee is eligible for promotion.

        Returns:
            bool: True if performance score > 85 and has at least 2 reviews
        """
        return self.performance_score > 85 and len(self._reviews) >= 2

    # Magic Methods for Object Comparison
    def __eq__(self, other) -> bool:
        """Compare employees by hourly rate."""
        if not isinstance(other, Employee):
            return NotImplemented
        return self.hourly_rate == other.hourly_rate

    def __lt__(self, other) -> bool:
        """Compare employees by hourly rate for sorting."""
        if not isinstance(other, Employee):
            return NotImplemented
        return self.hourly_rate < other.hourly_rate

    def __gt__(self, other) -> bool:
        """Compare employees by hourly rate."""
        if not isinstance(other, Employee):
            return NotImplemented
        return self.hourly_rate > other.hourly_rate

    def __str__(self) -> str:
        """String representation of the Employee."""
        return f"Employee: {self.name} ({self.employee_id}) - ${self.hourly_rate:.2f}/hour"

    def __repr__(self) -> str:
        """Official string representation of the Employee."""
        return f"{type(self).__name__}('{self.name}', '{self.employee_id}', {self.hourly_rate})"

    # Class Methods for Company Management
    @classmethod
    def add_employee(cls, employee: 'Employee') -> None:
        """
        Add an employee to the company roster.

        Args:
            employee: Employee object to add
        """
        # Use "is" (same object), not "in" — "in" would use __eq__,
        # which treats two different people with the same rate as equal
        if not any(existing is employee for existing in cls._all_employees):
            cls._all_employees.append(employee)

    @classmethod
    def get_total_payroll(cls, hours_worked: float) -> float:
        """
        Calculate total payroll for all employees.

        Args:
            hours_worked (float): Hours worked by each employee

        Returns:
            float: Total payroll amount
        """
        total = 0.0
        for employee in cls._all_employees:
            try:
                # Polymorphism: each type runs its OWN calculate_pay
                total += employee.calculate_pay(hours_worked)
            except InvalidHoursError as e:
                print(f"Skipping {employee.name} in payroll total: {e}")
        return total

    @classmethod
    def get_employees_by_type(cls, employee_type: str) -> List['Employee']:
        """
        Get employees by type.

        Args:
            employee_type (str): "fulltime", "parttime", or "base"

        Returns:
            List of employees of the specified type
        """
        employee_type = employee_type.lower()
        if employee_type == "fulltime":
            return [e for e in cls._all_employees if isinstance(e, FullTimeEmployee)]
        if employee_type == "parttime":
            return [e for e in cls._all_employees if isinstance(e, PartTimeEmployee)]
        if employee_type == "base":
            # type(...) is Employee excludes the subclasses
            return [e for e in cls._all_employees if type(e) is Employee]
        raise ValueError(f"Unknown employee type: {employee_type}")

    @classmethod
    def get_top_performers(cls, min_score: float = 90.0) -> List['Employee']:
        """
        Get employees with high performance scores.

        Args:
            min_score (float): Minimum performance score threshold

        Returns:
            List of high-performing employees
        """
        return [e for e in cls._all_employees if e.performance_score >= min_score]


class FullTimeEmployee(Employee):
    """
    Full-time employee with overtime pay and comprehensive benefits.

    Inherits from Employee and adds overtime calculation and benefits.
    """

    def __init__(self, name: str, employee_id: str, hourly_rate: float,
                 health_insurance: bool = True, retirement_401k: bool = True):
        """
        Initialize a FullTimeEmployee.

        Args:
            name (str): Employee name
            employee_id (str): Employee ID
            hourly_rate (float): Hourly rate
            health_insurance (bool): Health insurance coverage
            retirement_401k (bool): 401k retirement plan enrollment
        """
        # Let Employee handle name, ID, rate, validation, roster
        super().__init__(name, employee_id, hourly_rate)
        # Then add the full-time-only details
        self.health_insurance = health_insurance
        self.retirement_401k = retirement_401k

    @log_employee_action
    @validate_positive_hours
    def calculate_pay(self, hours_worked: float) -> float:
        """
        Calculate pay with overtime (1.5x rate for hours > 40).

        Args:
            hours_worked (float): Hours worked

        Returns:
            float: Total pay including overtime
        """
        regular_hours = min(hours_worked, 40)
        overtime_hours = max(hours_worked - 40, 0)
        return (regular_hours * self.hourly_rate
                + overtime_hours * self.hourly_rate * 1.5)

    @log_employee_action
    def calculate_benefits(self, hours_worked: float) -> float:
        """
        Calculate comprehensive benefits for full-time employee.

        Args:
            hours_worked (float): Hours worked this period

        Returns:
            float: Total benefits value
        """
        benefits = 0.0

        if self.health_insurance:
            benefits += 200.0

        if self.retirement_401k:
            gross_pay = self.calculate_pay(hours_worked)
            benefits += gross_pay * 0.05

        # 2 vacation hours per full 40-hour week, valued at the hourly rate
        weeks_worked = hours_worked / 40
        benefits += 2 * weeks_worked * self.hourly_rate

        return benefits

    @property
    def benefits_summary(self) -> Dict[str, Union[bool, float]]:
        """
        Get summary of benefits enrollment.

        Returns:
            Dictionary with benefit details
        """
        annual = 0.0
        if self.health_insurance:
            annual += 200.0 * 12
        if self.retirement_401k:
            annual += self.annual_salary_estimate * 0.05
        annual += 2 * 52 * self.hourly_rate  # vacation

        return {
            "health_insurance": self.health_insurance,
            "retirement_401k": self.retirement_401k,
            "estimated_annual_benefits": annual,
        }

    def __str__(self) -> str:
        """String representation of FullTimeEmployee."""
        return f"FullTime Employee: {self.name} ({self.employee_id}) - ${self.hourly_rate:.2f}/hour"


class PartTimeEmployee(Employee):
    """
    Part-time employee with hour limits and limited benefits.

    Inherits from Employee and adds hour restrictions and basic benefits.
    """

    def __init__(self, name: str, employee_id: str, hourly_rate: float,
                 max_hours_per_week: int = 20):
        """
        Initialize a PartTimeEmployee.

        Args:
            name (str): Employee name
            employee_id (str): Employee ID
            hourly_rate (float): Hourly rate
            max_hours_per_week (int): Maximum hours allowed per week
        """
        super().__init__(name, employee_id, hourly_rate)
        self.max_hours_per_week = max_hours_per_week

    @log_employee_action
    @validate_positive_hours
    def calculate_pay(self, hours_worked: float) -> float:
        """
        Calculate pay with hour limit enforcement.

        Args:
            hours_worked (float): Hours worked

        Returns:
            float: Total pay

        Raises:
            InvalidHoursError: If hours exceed weekly limit
        """
        if hours_worked > self.max_hours_per_week:
            raise InvalidHoursError(
                f"Part-time employee cannot work more than {self.max_hours_per_week} "
                f"hours per week, got {hours_worked}"
            )
        return self.hourly_rate * hours_worked

    @log_employee_action
    def calculate_benefits(self, hours_worked: float) -> float:
        """
        Calculate limited benefits for part-time employee.

        Args:
            hours_worked (float): Hours worked this period

        Returns:
            float: Limited benefits value
        """
        # 1 vacation hour per full part-time week, valued at the hourly rate
        weeks_worked = hours_worked / self.max_hours_per_week
        return 1 * weeks_worked * self.hourly_rate

    @property
    def weekly_hour_limit(self) -> int:
        """Get the weekly hour limit."""
        return self.max_hours_per_week

    def can_work_additional_hours(self, current_hours: float, additional_hours: float) -> bool:
        """
        Check if employee can work additional hours without exceeding limit.

        Args:
            current_hours (float): Hours already worked this week
            additional_hours (float): Additional hours requested

        Returns:
            bool: True if additional hours can be worked
        """
        return current_hours + additional_hours <= self.max_hours_per_week

    def __str__(self) -> str:
        """String representation of PartTimeEmployee."""
        return (f"PartTime Employee: {self.name} ({self.employee_id}) - "
                f"${self.hourly_rate:.2f}/hour (max {self.max_hours_per_week} hours/week)")


# Utility Functions for Demonstration
def demonstrate_polymorphism():
    """
    Demonstrate polymorphism with different employee types.

    Shows how different employee objects can be treated uniformly
    through their common interface.
    """
    print("=== Polymorphism Demonstration ===")
    staff = [
        Employee("John Doe", "EMP001", 20.00),
        FullTimeEmployee("Jane Smith", "FT001", 30.00),
        PartTimeEmployee("Bob Johnson", "PT001", 18.00, max_hours_per_week=25),
    ]
    hours = 35

    # Same two method calls for everyone — each type reacts in its own way
    for person in staff:
        try:
            pay = person.calculate_pay(hours)
            benefits = person.calculate_benefits(hours)
            print(f"{person.name}: Pay=${pay:.2f}, Benefits=${benefits:.2f}")
        except InvalidHoursError as e:
            print(f"{person.name}: Error - {e}")


def demonstrate_decorators():
    """
    Demonstrate the custom decorators in action.

    Shows how decorators modify function behavior for logging and validation.
    """
    print("=== Decorator Demonstration ===")
    worker = FullTimeEmployee("Alice Cooper", "FT002", 35.00)

    print("Testing valid hours:")
    worker.calculate_pay(40)

    print("\nTesting invalid hours:")
    for bad_hours in (-5, 200):
        try:
            worker.calculate_pay(bad_hours)
        except InvalidHoursError as e:
            print(f"Validation caught: {e}")


def generate_company_report():
    """
    Generate a comprehensive company report showing all employees.

    Demonstrates class methods and polymorphism.
    """
    print("=== Company Report ===")
    print(f"Total Employees: {len(Employee._all_employees)}")
    print(f"Full-time: {len(Employee.get_employees_by_type('fulltime'))}")
    print(f"Part-time: {len(Employee.get_employees_by_type('parttime'))}")
    print(f"Base: {len(Employee.get_employees_by_type('base'))}")

    payroll = Employee.get_total_payroll(40)
    print(f"Total Weekly Payroll (40 hours): ${payroll:.2f}")

    top = Employee.get_top_performers(85.0)
    print(f"Top Performers (>85%): {len(top)}")
    for person in top:
        print(f"  - {person.name}: {person.performance_score}%")


# Test code
if __name__ == "__main__":
    print("=== Employee Management System ===\n")

    # Step 1: Test basic Employee class
    print("1. Testing basic Employee creation:")
    try:
        emp = Employee("Alice Smith", "EMP001", 25.50)
        print(emp)
        try:
            Employee("Bad Id", "123", 20.0)
        except InvalidEmployeeDataError as e:
            print(f"Validation works: {e}")
    except Exception as e:
        print(f"Caught expected error: {e}")

    print("\n2. Testing FullTimeEmployee with overtime:")
    try:
        ft_emp = FullTimeEmployee("Jane Doe", "FT001", 30.00)
        print(ft_emp)
        regular = ft_emp.calculate_pay(40)
        overtime = ft_emp.calculate_pay(45)
        print(f"Regular pay (40 hrs): ${regular:.2f}")
        print(f"Overtime pay (45 hrs): ${overtime:.2f}")
        benefits = ft_emp.calculate_benefits(40)
        print(f"Benefits: ${benefits:.2f}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n3. Testing PartTimeEmployee with hour limits:")
    try:
        pt_emp = PartTimeEmployee("Carol White", "PT001", 20.00, max_hours_per_week=25)
        print(pt_emp)
        normal = pt_emp.calculate_pay(20)
        print(f"Normal pay (20 hrs): ${normal:.2f}")
        try:
            pt_emp.calculate_pay(30)
        except InvalidHoursError as e:
            print(f"Hour limit enforcement works: {e}")
        benefits = pt_emp.calculate_benefits(20)
        print(f"Benefits: ${benefits:.2f}")
    except Exception as e:
        print(f"Caught expected error: {e}")

    print("\n4. Testing company-wide operations:")
    total = Employee.get_total_payroll(40)
    print(f"Total company payroll (40 hrs): ${total:.2f}")
    print(f"Full-time employees: {len(Employee.get_employees_by_type('fulltime'))}")
    print(f"Part-time employees: {len(Employee.get_employees_by_type('parttime'))}")

    print("\n5. Testing performance tracking:")
    emp.add_performance_review(92, "Excellent work")
    emp.add_performance_review(88, "Great improvement")
    print(f"{emp.name}'s performance score: {emp.performance_score}")
    print(f"Promotion eligible: {emp.get_promotion_eligibility()}")

    print("\n6. Demonstrating polymorphism:")
    demonstrate_polymorphism()

    print("\n7. Demonstrating decorators:")
    demonstrate_decorators()

    print("\n8. Company Report:")
    generate_company_report()
