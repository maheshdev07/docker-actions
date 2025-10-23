import re

gstin = '06AAACG1840M2ZO'
print('GSTIN:', gstin)
print('Length:', len(gstin))
print('Char breakdown:')
for i, c in enumerate(gstin):
    print(f'{i}: {c}')

pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[0-9A-Z]{1}[0-9A-Z]{1}$'
print('Pattern:', pattern)
print('Match:', bool(re.match(pattern, gstin.upper())))

# Let's check each part
print('\nPattern breakdown:')
print('^[0-9]{2} - First 2 digits:', gstin[0:2])
print('[A-Z]{5} - Next 5 letters:', gstin[2:7])
print('[0-9]{4} - Next 4 digits:', gstin[7:11])
print('[A-Z]{1} - Next 1 letter:', gstin[11:12])
print('[0-9A-Z]{1} - Next 1 alphanumeric:', gstin[12:13])
print('[0-9A-Z]{1}$ - Last 1 alphanumeric:', gstin[13:14])

# Test with a known valid GSTIN
valid_gstin = '27AAPFU0939F1ZV'
print(f'\nTesting known valid GSTIN: {valid_gstin}')
print('Match:', bool(re.match(pattern, valid_gstin.upper())))
