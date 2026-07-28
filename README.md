New Features:
Phase 1 :(April): Done
1. Upgrade to latest Django 5.2.13
2. Upgrade to use Bootstrap 5.3.8
3. Change transaction screen to mobile friendly format
4. Order latest transaction to be on top
5. Add PDF/csv export to transaction screen
6. Install in new Lightsail instance and attach to www.velvasam.net URL

Phase 2 (May-June):
1. Change Beneficiary, Profile to mobile friendly
2. Change Project, past Project to use Toast similar to Transactions mobile format
3. Fix Report menu
4. The home page is to show the following
   - A Bar chart of each project and total funds donated

Phase 3 (May-June):
1. Allow multi-currency for transactions
    - Add currency field for Bank class and allow major currencies (USD,GBP,EURO,LKR) in drop down, Default LKR
    - Enhance calculations to show Balance of Bank accounts
    - Add amounLocal field for transaction default=amount. 
    - Transaction screen to show currency
2. Update existing data to reflect multi-currency
    - There are few projects have remarks about this information.

Phase 4 (July-Aug)
5. Allow Beneficiaries table to handle group. 
    - Ability to group beneficiaries into single group 
6. Allow photo uploads and show that in Home page.
7. Create login for each donor and donor able to see the funded transactions.
