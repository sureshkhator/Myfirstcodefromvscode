import periodictable as pt

name = input("Enter element name or symbol: ")

# Try a few common lookup strategies: as-provided, lowercase (module uses lowercase names),
# uppercase (symbols), and capitalized. Fall back to scanning module attrs by element.name.
element = getattr(pt, name, None)
if element is None:
    element = getattr(pt, name.lower(), None)
if element is None:
    element = getattr(pt, name.capitalize(), None)
if element is None:
    element = getattr(pt, name.upper(), None)

if element is None:
    # fallback: look for an object whose .name matches the input (case-insensitive)
    for attr in dir(pt):
        try:
            obj = getattr(pt, attr)
        except Exception:
            continue
        if hasattr(obj, "name") and obj.name:
            try:
                if obj.name.lower() == name.lower():
                    element = obj
                    break
            except Exception:
                continue

if element:
    print("Name:", element.name)
    print("Symbol:", element.symbol)
    print("Atomic Number:", element.number)
    print("Atomic Weight:", element.mass)
    print("Density:", element.density)
else:
    print("Element not found.")