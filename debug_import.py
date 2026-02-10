
try:
    import backend.services.alerts.service as service
    print("Import successful")
    print(f"Has PriceAlertDAO: {hasattr(service, 'PriceAlertDAO')}")
except Exception as e:
    print(f"Import failed: {e}")
    import traceback
    traceback.print_exc()
