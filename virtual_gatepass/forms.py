from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.models import User
from .models import Student, Counsellor, HOD, GatePass, DEPARTMENTS, COURSE_YEARS, COURSE_SEMESTERS


# ------------------ STUDENT REGISTRATION ------------------
class StudentRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    usn = forms.CharField(max_length=15, label="USN")
    course_year = forms.ChoiceField(choices=COURSE_YEARS, label="Course Year")
    course_semester = forms.ChoiceField(choices=COURSE_SEMESTERS, label="Semester")
    department = forms.ChoiceField(choices=DEPARTMENTS, label="Department")
    phone = forms.CharField(max_length=15, label="Student Phone Number")
    parent_phone = forms.CharField(max_length=15, label="Parent Phone Number")

    counsellor = forms.ModelChoiceField(
        queryset=Counsellor.objects.none(),
        required=True,
        label="Counsellor (Select from your department)"
    )

    class Meta:
        model = User
        fields = [
            'username', 'first_name', 'last_name', 'email',
            'password1', 'password2'
        ]

    def __init__(self, *args, **kwargs):
        """
        Dynamically filter counsellors based on selected department.
        """
        department_selected = kwargs.pop('department_selected', None)
        super().__init__(*args, **kwargs)

        # Dynamically set counsellor queryset
        if department_selected:
            self.fields['counsellor'].queryset = Counsellor.objects.filter(department=department_selected)
        else:
            self.fields['counsellor'].queryset = Counsellor.objects.all()

        # Apply consistent Bootstrap styling
        for field in self.fields.values():
            if not isinstance(field.widget, forms.CheckboxInput):
                field.widget.attrs.update({'class': 'form-control'})

    def save(self, commit=True):
        """
        Automatically link the student with the correct HOD and Counsellor.
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']

        if commit:
            user.save()
            department = self.cleaned_data['department']
            counsellor = self.cleaned_data['counsellor']
            hod = HOD.objects.filter(department=department).first()

            Student.objects.create(
                user=user,
                usn=self.cleaned_data['usn'],
                course_year=self.cleaned_data['course_year'],
                course_semester=self.cleaned_data['course_semester'],
                department=department,
                phone=self.cleaned_data['phone'],
                parent_phone=self.cleaned_data['parent_phone'],
                counsellor=counsellor,
                hod=hod,
            )
        return user


# ------------------ COUNSELLOR REGISTRATION ------------------
class CounsellorRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    eid = forms.CharField(max_length=20, label="Employee ID")
    department = forms.ChoiceField(choices=DEPARTMENTS, label="Department")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            Counsellor.objects.create(
                user=user,
                eid=self.cleaned_data['eid'],
                department=self.cleaned_data['department'],
            )
        return user


# ------------------ HOD REGISTRATION ------------------
class HODRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    eid = forms.CharField(max_length=20, label="Employee ID")
    department = forms.ChoiceField(choices=DEPARTMENTS, label="Department")

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
            HOD.objects.create(
                user=user,
                eid=self.cleaned_data['eid'],
                department=self.cleaned_data['department'],
            )
        return user


# ------------------ LOGIN FORM ------------------
class LoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Username'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Enter Password'})
    )


# ------------------ GATEPASS FORM ------------------
class GatePassForm(forms.ModelForm):
    """
    Used by students to apply for a new gate pass.
    Includes from_date and to_date fields.
    """
    from_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True,
        label="From Date"
    )
    to_date = forms.DateField(
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        required=True,
        label="To Date"
    )

    class Meta:
        model = GatePass
        fields = ['from_date', 'to_date', 'course_year', 'course_semester', 'counsellor', 'reason']
        widgets = {
            'course_year': forms.Select(attrs={'class': 'form-select'}),
            'course_semester': forms.Select(attrs={'class': 'form-select'}),
            'counsellor': forms.Select(attrs={'class': 'form-select'}),
            'reason': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter reason clearly'
            }),
        }

    def __init__(self, *args, **kwargs):
        student = kwargs.pop('student', None)
        super().__init__(*args, **kwargs)
        if student:
            # Only counsellors from the same department as student
            self.fields['counsellor'].queryset = Counsellor.objects.filter(department=student.department)
        else:
            self.fields['counsellor'].queryset = Counsellor.objects.all()
