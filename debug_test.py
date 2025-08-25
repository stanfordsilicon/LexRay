expanded_options = ['dd/y', 'MM/y', 'yy/y']
english_values = ['M/y']

print('Testing validation logic...')
print('Expanded options:', expanded_options)
print('English values:', english_values)

# First try exact matches
confirmed = [opt for opt in expanded_options if opt in english_values or len(set(opt.lower())) == 1]
print('Exact matches:', confirmed)

# If no exact matches, try to find the best approximation
if not confirmed:
    print('No exact matches, applying fallback...')
    for opt in expanded_options:
        print(f'Checking option: {opt}')
        if opt == 'MM/y':
            print('Found MM/y, should select it')
            confirmed = ['MM/y']
            break
        elif opt in ['dd/y'] and 'M/y' in english_values:
            print('Found dd/y, falling back to M/y')
            confirmed = ['M/y']
            break
        elif opt in ['MMM y', 'MMMM y'] and 'M/y' in english_values:
            print('Found MMM y or MMMM y, falling back to M/y')
            confirmed = ['M/y']
            break

print('Final confirmed:', confirmed)
