import pyvisa

rm = pyvisa.ResourceManager()
resources = rm.list_resources()
print("Select resource:")
inst = None
while not (choice < len(resources) and choice >= 0):
    for i, resource in enumerate(resources):
        print(str(i+1) + '.', resource)
    choice = int(input("Selection: ")) - 1
    if not (choice < len(resources) and choice >= 0): print("Invalid selection")
    else:
        inst = rm.open_resource(resources[choice], read_terminator='\n', baud_rate=57600)
        print('Selected: ', inst)
        idn = inst.query('*IDN?')
        if 'Chroma' not in idn and '63802' not in idn:
            print('You did not select a Chroma Load Emulator');
print('outside')
