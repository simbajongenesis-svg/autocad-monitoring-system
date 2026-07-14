from django.db import models


class PanelRecord(models.Model):
    BOX_TYPE_CHOICES = [
        ('nema1', 'NEMA 1'),
        ('nema3r', 'NEMA 3R'),
        ('nema12', 'NEMA 12'),
        ('nema4x', 'NEMA 4X'),
        ('itemonly', 'Item Only'),
        ('others', 'Others'),
    ]

    COLOR_CHOICES = [
        ('gray_wrinkle', 'Gray Wrinkle'),
        ('beige_wrinkle', 'Beige Wrinkle'),
        ('black_wrinkle', 'Black Wrinkle'),
        ('blue_wrinkle', 'Blue Wrinkle'),
        ('green_wrinkle', 'Green Wrinkle'),
        ('light_gray_wrinkle', 'Light Gray Wrinkle'),
        ('orange_wrinkle', 'Orange Wrinkle'),
        ('red_wrinkle', 'Red Wrinkle'),
        ('white_wrinkle', 'White Wrinkle'),
        ('yellow_wrinkle', 'Yellow Wrinkle'),
        ('stainless_steel', 'Stainless Steel'),
        ('item_only', 'Item Only'),
        ('others', 'Others'),
    ]

    date = models.DateField()
    fq_number = models.CharField(max_length=50)
    jo_number = models.CharField(max_length=50)
    panel_name = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    received_by = models.CharField(max_length=100)
    box_type = models.CharField(max_length=20, choices=BOX_TYPE_CHOICES)
    main_cb = models.CharField(max_length=100)
    cb_model = models.CharField(max_length=100)
    color = models.CharField(max_length=20, choices=COLOR_CHOICES)
    remarks = models.TextField(blank=True, null=True)
    is_archived = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.customer_name} with FQ#: {self.fq_number} dated: {self.date}"

#note hint: “hint is monitoring app panel records”