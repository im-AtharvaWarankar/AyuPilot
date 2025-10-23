from atomicloops.filters import AtomicDateFilter
from .models import Users


class UsersFilter(AtomicDateFilter):
    class Meta:
        model = Users
        fields = (
            'createdAt',
            'updatedAt',
            'is_active',
            'is_superuser',
            'is_staff',
            'level'
        )


# ============================================================================
# COMMENTED OUT: UsersDevicesFilter not needed for AyuPilot Healthcare Application
# ============================================================================

# class UsersDevicesFilter(AtomicDateFilter):
#     class Meta:
#         model = UsersDevices
#         fields = (
#             'createdAt',
#             'updatedAt',
#             'userId',
#         )
