import pkgutil
import inspect
import robocode_tank_royale.bot_api as bot_api
import robocode_tank_royale.schema as schema

print("=" * 80)
print("BOT_API MODULES")
print("=" * 80)
modules = [m.name for m in pkgutil.iter_modules(bot_api.__path__)]
print("Submodules:", modules)

print("\nDirect imports from bot_api:")
imports = [x for x in dir(bot_api) if not x.startswith("_")]
for imp in imports:
    obj = getattr(bot_api, imp)
    if inspect.isclass(obj):
        print(f"  Class: {imp}")
    elif inspect.isfunction(obj):
        print(f"  Function: {imp}")
    elif inspect.ismodule(obj):
        print(f"  Module: {imp}")
    else:
        print(f"  {type(obj).__name__}: {imp}")

print("\n" + "=" * 80)
print("SCHEMA MODULES")
print("=" * 80)
modules_schema = [m.name for m in pkgutil.iter_modules(schema.__path__)]
print("Submodules:", modules_schema)

print("\nDirect imports from schema:")
imports_schema = [x for x in dir(schema) if not x.startswith("_")]
for imp in imports_schema:
    obj = getattr(schema, imp)
    if inspect.isclass(obj):
        print(f"  Class: {imp}")
    elif inspect.isfunction(obj):
        print(f"  Function: {imp}")
    elif inspect.ismodule(obj):
        print(f"  Module: {imp}")
    else:
        print(f"  {type(obj).__name__}: {imp}")

print("\n" + "=" * 80)
print("DETAILED BOT_API EXPLORATION")
print("=" * 80)

# Check each submodule in bot_api
for mod_name in modules:
    mod = __import__(f"robocode_tank_royale.bot_api.{mod_name}", fromlist=[mod_name])
    print(f"\nModule: robocode_tank_royale.bot_api.{mod_name}")
    items = [x for x in dir(mod) if not x.startswith("_")]
    for item in items[:20]:  # Limit output
        obj = getattr(mod, item)
        if inspect.isclass(obj):
            print(f"  Class: {item}")
        elif inspect.isfunction(obj):
            print(f"  Function: {item}")
        else:
            print(f"  {type(obj).__name__}: {item}")
    if len(items) > 20:
        print(f"  ... and {len(items) - 20} more items")

print("\n" + "=" * 80)
print("DETAILED SCHEMA EXPLORATION")
print("=" * 80)

# Check each submodule in schema
for mod_name in modules_schema:
    mod = __import__(f"robocode_tank_royale.schema.{mod_name}", fromlist=[mod_name])
    print(f"\nModule: robocode_tank_royale.schema.{mod_name}")
    items = [x for x in dir(mod) if not x.startswith("_")]
    for item in items[:20]:  # Limit output
        obj = getattr(mod, item)
        if inspect.isclass(obj):
            print(f"  Class: {item}")
        elif inspect.isfunction(obj):
            print(f"  Function: {item}")
        else:
            print(f"  {type(obj).__name__}: {item}")
    if len(items) > 20:
        print(f"  ... and {len(items) - 20} more items")
