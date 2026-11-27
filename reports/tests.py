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
    def _create_transaction(
        cls,
        bank,
        beneficiary,
        project,
        expense_type,
        amount,
        year,
        tx_type=Transaction.TxType_DEPOSIT,
    ):
        Transaction.objects.create(
            bank=bank,
            owner=cls.user,
            project=project,
            txType=tx_type,
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

    def test_only_deposits_with_contribution_categories_count_as_contributions(self):
        project_type = ProjectType.objects.get(description='Community')
        bank = Transaction.objects.first().bank
        beneficiary = Transaction.objects.first().beneficiary
        monthly_contribution = ExpenseType.objects.create(
            expense='Monthly Contribution',
            prjType=project_type,
        )
        contribution = ExpenseType.objects.get(expense='Contribution')

        self._create_transaction(
            bank, beneficiary, self.project, monthly_contribution, 25, 2024
        )
        self._create_transaction(
            bank,
            beneficiary,
            self.project,
            contribution,
            30,
            2024,
            tx_type=Transaction.TxType_WITHDRWAL,
        )

        response = self.client.get(reverse('reports:contributionDistribution'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['chart_data']['contributions'], [125.0, 60.0])
        self.assertEqual(response.context['chart_data']['distributions'], [70.0, 0.0])
        self.assertContains(response, 'id="contribution-distribution-chart"')
        self.assertContains(response, 'contribution-distribution-chart-container')
        self.assertNotContains(response, 'id="containerMonthlyAvg"')
        self.assertNotContains(response, 'id="containerMonthly"')
        self.assertContains(response, 'aria-label="Dashboard reports"')
        self.assertContains(response, 'Contribution &amp; Distribution')
        self.assertNotContains(response, 'Annual Contribution &amp; Distribution')
        self.assertContains(response, 'Contribution by Category')
        self.assertContains(response, 'Expense by Category')
        self.assertContains(response, 'Beneficiaries Report')
        self.assertNotContains(response, 'Highcharts')

    def test_report_uses_transaction_amount_when_local_amount_is_zero(self):
        transaction = Transaction.objects.filter(project=self.project).first()
        Transaction.objects.filter(pk=transaction.pk).update(
            amount=125,
            amountLocal=0,
        )

        response = self.client.get(reverse('reports:contributionDistribution'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['chart_data']['contributions'], [125.0, 60.0])
        self.assertEqual(response.context['chart_data']['distributions'], [40.0, 0.0])

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

    def test_project_without_transactions_does_not_show_an_unfiltered_chart(self):
        project_type = ProjectType.objects.get(description='Community')
        empty_project = Project.objects.create(
            name='Unused project',
            updatedBy=self.user,
            prjType=project_type,
        )

        response = self.client.get(
            reverse('reports:contributionDistribution'),
            {'project': empty_project.pk},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['chart_data']['labels'], [])
        self.assertContains(response, 'No transaction data is available for this selection.')
        self.assertNotContains(response, 'id="containerMonthly"')

    def test_annual_contribution_distribution_tab_sums_all_projects_in_lkr(self):
        response = self.client.get(reverse('reports:annualContributionDistribution'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'annual_contribution_distribution.html')
        self.assertEqual(response.context['chart_data']['labels'], [2024, 2025])
        self.assertEqual(response.context['chart_data']['contributions'], [100.0, 60.0])
        self.assertEqual(response.context['chart_data']['distributions'], [40.0, 0.0])
        self.assertContains(response, 'Amounts are shown in LKR')
        self.assertContains(response, 'class="nav-link active"')

    def test_expense_by_category_uses_the_same_summary_as_first_tab_pie(self):
        ReportByMonth.objects.create(
            year=2024,
            month='Jan',
            exType='Distribution ',
            amount=4000,
        )
        ReportByMonth.objects.create(
            year=2024,
            month='Jan',
            exType='Contribution ',
            amount=9000,
        )
        ReportByMonth.objects.create(
            year=2024,
            month='Feb',
            exType='Monthly Contribution ',
            amount=2000,
        )

        response = self.client.get(reverse('reports:expenseByCategory'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'expense_by_category.html')
        self.assertEqual(response.context['chart_data'], {
            'labels': ['Distribution'],
            'values': [4000.0],
        })
        self.assertContains(response, 'Expense totals by category for all years')
        self.assertNotContains(response, 'Expense report by year')
        self.assertNotContains(response, 'expense-by-category-all-years-chart')
        self.assertContains(response, 'Amount</th>')
        self.assertContains(response, 'class="nav-link active"')

    def test_expense_by_category_year_tabs_filter_totals_and_all_years(self):
        ReportByMonth.objects.create(
            year=2024,
            month='Jan',
            exType='Distribution ',
            amount=4000,
        )
        ReportByMonth.objects.create(
            year=2025,
            month='Jan',
            exType='Distribution',
            amount=6000,
        )
        ReportByMonth.objects.create(
            year=2025,
            month='Jan',
            exType='Contribution',
            amount=9000,
        )
        ReportByMonth.objects.create(
            year=2024,
            month='Jan',
            exType='Monthly Contribution',
            amount=2000,
        )

        all_years_response = self.client.get(reverse('reports:expenseByCategory'))
        self.assertEqual(all_years_response.status_code, 200)
        self.assertEqual(all_years_response.context['selected_year'], None)
        self.assertEqual(all_years_response.context['chart_data'], {
            'labels': ['Distribution'],
            'values': [10000.0],
        })
        self.assertContains(all_years_response, 'href="?year=all"')
        self.assertContains(all_years_response, 'href="?year=2025"')
        self.assertContains(all_years_response, 'href="?year=2024"')

        year_response = self.client.get(
            reverse('reports:expenseByCategory'),
            {'year': 2024},
        )
        self.assertEqual(year_response.status_code, 200)
        self.assertEqual(year_response.context['selected_year'], 2024)
        self.assertEqual(year_response.context['chart_data'], {
            'labels': ['Distribution'],
            'values': [4000.0],
        })
        self.assertContains(year_response, 'Expense by Category - 2024')


class AnnualContributionPageTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user(username='annual-contribution-user')
        project_type = ProjectType.objects.create(description='Annual report')
        cls.project = Project.objects.create(
            name='Annual report project',
            updatedBy=cls.user,
            prjType=project_type,
        )
        cls.bank = BankAccount.objects.create(
            holder=cls.user,
            name='Annual report account',
            bank='Test bank',
            accNumber='789',
            branch='Main',
            routing='012',
            updatedBy=cls.user,
        )
        cls.beneficiary = Beneficiary.objects.create(
            name='Annual report beneficiary',
            accountHolder='Annual report beneficiary',
            amount=0,
            category='Student',
            updatedBy=cls.user,
        )
        cls.contribution = ExpenseType.objects.create(
            expense='Contribution',
            prjType=project_type,
        )
        cls.monthly_contribution = ExpenseType.objects.create(
            expense='Monthly Contribution',
            prjType=project_type,
        )
        cls.expense = ExpenseType.objects.create(
            expense='Distribution',
            prjType=project_type,
        )

    def create_transaction(self, expense_type, amount, year, tx_type=Transaction.TxType_DEPOSIT):
        return Transaction.objects.create(
            bank=self.bank,
            owner=self.user,
            project=self.project,
            txType=tx_type,
            exType=expense_type,
            beneficiary=self.beneficiary,
            amount=amount,
            amountLocal=amount,
            date=f'{year}-06-01',
            updatedBy=self.user,
        )

    def test_annual_contribution_displays_a_chart_and_category_totals(self):
        self.create_transaction(self.monthly_contribution, 120, 2025)
        self.create_transaction(self.monthly_contribution, 80, 2025)
        self.create_transaction(self.expense, 250, 2025)

        response = self.client.get(reverse('reports:annualContribution'))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'annual_contribution.html')
        self.assertEqual(response.context['selected_year'], 2025)
        self.assertEqual(
            response.context['chart_data'],
            {'labels': ['Monthly Contribution'], 'values': [200.0]},
        )

    def test_annual_contribution_year_tabs_filter_category_totals(self):
        self.create_transaction(self.monthly_contribution, 120, 2024)
        self.create_transaction(self.monthly_contribution, 200, 2025)
        self.create_transaction(self.expense, 50, 2025)

        response = self.client.get(
            reverse('reports:annualContribution'),
            {'year': 2024},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['years'], [2025, 2024])
        self.assertEqual(response.context['selected_year'], 2024)
        self.assertEqual(
            response.context['chart_data'],
            {'labels': ['Monthly Contribution'], 'values': [120.0]},
        )
        self.assertContains(response, 'href="?year=2025"')
        self.assertContains(response, 'href="?year=2024"')

    def test_annual_contribution_all_years_tab_sums_each_category(self):
        self.create_transaction(self.monthly_contribution, 120, 2024)
        self.create_transaction(self.monthly_contribution, 200, 2025)
        self.create_transaction(self.expense, 50, 2025)
        self.create_transaction(
            self.contribution,
            300,
            2025,
            tx_type=Transaction.TxType_WITHDRWAL,
        )

        response = self.client.get(
            reverse('reports:annualContribution'),
            {'year': 'all'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context['selected_year'])
        self.assertTrue(response.context['all_years_selected'])
        self.assertEqual(
            response.context['chart_data'],
            {
                'labels': ['Monthly Contribution'],
                'values': [320.0],
            },
        )
        self.assertContains(response, 'Annual Contribution by Category - All Years')
        self.assertContains(response, 'href="?year=all"')
        self.assertContains(response, 'class="nav-link active"')

    def test_annual_contribution_excludes_withdrawals_categorized_as_contributions(self):
        self.create_transaction(self.contribution, 150, 2025)
        self.create_transaction(
            self.monthly_contribution,
            300,
            2025,
            tx_type=Transaction.TxType_WITHDRWAL,
        )

        response = self.client.get(reverse('reports:annualContribution'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['chart_data'],
            {'labels': ['Contribution'], 'values': [150.0]},
        )

    def test_annual_contribution_amounts_use_comma_separators(self):
        self.create_transaction(self.monthly_contribution, 1234567, 2025)

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
        self.assertContains(response, 'Past')
        self.assertNotContains(response, 'Inactive')
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
