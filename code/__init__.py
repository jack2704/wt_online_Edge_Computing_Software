from pint import UnitRegistry
ur = UnitRegistry()
voltage = ur('V')
resistance = ur('ohm')
current = (voltage/resistance).to('A')

