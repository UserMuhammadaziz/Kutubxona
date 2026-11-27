from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from organization.models import TenantModel


class Review(TenantModel):
    """A reader's rating and opinion of a book they have read and returned."""

    book = models.ForeignKey("kitob.Kitob", on_delete=models.CASCADE, related_name="reviews")
    reader = models.ForeignKey("oquvchi.Oquvchi", on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    text = models.TextField(blank=True, max_length=1000)
    # Librarians hide offensive or off-topic reviews instead of deleting them.
    is_hidden = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        constraints = [models.UniqueConstraint(fields=["book", "reader"], name="review_one_per_reader_book")]

    def __str__(self):
        return f"{self.book_id} · {self.reader_id} · {self.rating}"
