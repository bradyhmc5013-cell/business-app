from datetime import date
import expense_core as et

print('--- Automated test start ---')
expenses = et.load_expenses()
print('Initial count:', len(expenses))
print('\nListing before test:')
et.list_expenses(expenses)

# Add
nid = et.next_id(expenses)
new = {
    'id': nid,
    'date': date.today().isoformat(),
    'vendor': 'AUTOTEST',
    'category': 'Other',
    'amount': 9.99,
    'notes': 'added by automated test',
    'receipt_path': ''
}
expenses.append(new)
et.save_expenses(expenses)
print(f"\nAdded expense #{nid}.")

expenses = et.load_expenses()
print('\nListing after add:')
et.list_expenses(expenses)

# Edit
e = et.find_by_id(expenses, nid)
if e:
    e['amount'] = 19.99
    e['vendor'] = 'AUTOTEST-EDIT'
    et.save_expenses(expenses)
    print(f"\nEdited expense #{nid}.")

expenses = et.load_expenses()
print('\nListing after edit:')
et.list_expenses(expenses)

# Delete
e = et.find_by_id(expenses, nid)
if e:
    expenses.remove(e)
    et.save_expenses(expenses)
    print(f"\nDeleted expense #{nid}.")

expenses = et.load_expenses()
print('\nListing after delete:')
et.list_expenses(expenses)
print('\n--- Automated test end ---')
