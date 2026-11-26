from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from accounts.models import (
    BankAccount,
    Beneficiary,
    ExpenseType,
    Project,
    ProjectType,
    Transaction,
)
from .models import ReportByMonth


class ContributionDistributionReportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='report-user')
        project_type = ProjectType.objects.create(description='Community')
        cls.project = Project.objects.create(
            name='Project One',
            updatedBy=cls.user,
            prjType=project_type,
        )
        other_project = Project.objects.create(
            name='Project Two',
            updatedBy=cls.user,
            prjType=project_type,
        )
        bank = BankAccount.objects.create(
            holder=cls.user,
            name='Test account',
            bank='Test bank',
            accNumber='123',
            branch='Main',
            routing='456',
            updatedBy=cls.user,
        )
        beneficiary = Beneficiary.objects.create(
            name='Test beneficiary',
            accountHolder='Test beneficiary',
            amount=0,
            category='Student',
            updatedBy=cls.user,
        )
        contribution = ExpenseType.objects.create(
            expense='Contribution',
            prjType=project_type,
        )
        distribution = ExpenseType.objects.create(
            expense='Distribution',
            prjType=project_type,
        )
        cls._create_transaction(bank, beneficiary, cls.project, contribution, 100, 2024)
        cls._create_transaction(bank, beneficiary, cls.project, distribution, 40, 2024)
        cls._create_transaction(bank, beneficiary, other_project, contribution, 60, 2025)

    @classmethod
    def _create_transaction(cls, bank, beneficiary, project, expense_type, amount, year):
        Transaction.objects.create(
            bank=bank,
            owner=cls.user,
            project=project,
            txType=Transaction.TxType_DEPOSIT,
            exType=expense_type,
            beneficiary=beneficiary,
            amount=amount,
            amountLocal=amount,
            date=f'{year}-06-01',
            updatedBy=cls.user,
        )

    def test_report_summarizes_all_projects_by_year(self):
        response = self.client.get(reverse('reports:contributionDistribution'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['chart_data']['labels'], [2024, 2025])
        self.assertEqual(response.context['chart_data']['contributions'], [100.0, 60.0])
        self.assertEqual(response.context['chart_data']['distributions'], [40.0, 0.0])
        self.assertContains(response, 'id="contribution-distribution-chart"')
        self.assertContains(response, 'contribution-distribution-chart-container')
        self.assertContains(response, 'id="containerMonthlyAvg"')
        self.assertContains(response, 'id="containerMonthly"')
        self.assertContains(response, 'aria-label="Dashboard reports"')
        self.assertContains(response, 'Contribution &amp; Distribution')
        self.assertContains(response, 'Annual Contribution')
        self.assertContains(response, 'Beneficiaries Report')
        self.assertNotContains(response, 'Highcharts')

    def test_dashboard_opens_the_contribution_distribution_tab(self):
        response = self.client.get(reverse('reports:dashboard'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'class="nav-link active"')
        self.assertContains(response, 'href="/reports/contribution-distribution/"')

    def test_report_can_be_filtered_to_one_project(self):
        response = self.client.get(
            reverse('reports:contributionDistribution'),
            {'project': self.project.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['chart_data']['labels'], [2024])
        self.assertEqual(response.context['chart_data']['contributions'], [100.0])
        self.assertEqual(response.context['chart_data']['distributions'], [40.0])


class AnnualContributionPageTests(TestCase):
    def test_annual_contribution_displays_a_chart_and_category_totals(self):
        ReportByMonth.objects.create(
            year=2025,
            month='Jan',
            exType='Monthly Contribution',
            amount=120,
        )
        ReportByMonth.objects.create(
            year=2025,
            month='Feb',
            exType='Monthly Contribution',
            amount=80,
        )

        response = self.client.get(reverse('reports:annualContribution'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'annual_contribution.html')
        self.assertEqual(
            response.context['chart_data'],
            {'labels': ['Monthly Contribution'], 'values': [200.0]},
        )

    def test_annual_contribution_amounts_use_comma_separators(self):
        ReportByMonth.objects.create(
            year=2025,
            month='Jan',
            exType='Monthly Contribution',
            amount=1234567.89,
        )

        response = self.client.get(reverse('reports:annualContribution'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, '1,234,567.89')


class BeneficiariesReportPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='beneficiary-report-user')
        Beneficiary.objects.create(
            name='Active student',
            accountHolder='Student',
            amount=100,
            category='Student',
            status='Active',
            updatedBy=cls.user,
        )
        Beneficiary.objects.create(
            name='Inactive student',
            accountHolder='Student',
            amount=100,
            category='Student',
            status='Inactive',
            updatedBy=cls.user,
        )
        Beneficiary.objects.create(
            name='Active patient',
            accountHolder='Patient',
            amount=100,
            category='Patient',
            status='Active',
            updatedBy=cls.user,
        )

    def test_beneficiaries_report_displays_counts_by_category_and_status(self):
        response = self.client.get(reverse('reports:beneficiariesReport'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'beneficiaries_report.html')
        self.assertEqual(response.context['total_beneficiaries'], 3)
        self.assertEqual(response.context['active_beneficiaries'], 2)
        self.assertEqual(response.context['inactive_beneficiaries'], 1)
        self.assertEqual(
            response.context['chart_data'],
            {
                'labels': ['Student', 'Teacher', 'Patient', 'Poverty'],
                'active': [1, 0, 1, 0],
                'inactive': [1, 0, 0, 0],
            },
        )
