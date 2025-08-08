from django.db import models

from django.db import models
from wagtail.models import Page
from wagtail.fields import RichTextField, StreamField
from wagtail import blocks
from wagtail.admin.panels import FieldPanel, MultiFieldPanel

class BlogIndexPage(Page):
    intro = RichTextField(blank=True)

    content_panels = Page.content_panels + [
        FieldPanel("intro"),
    ]

class BlogPostPage(Page):
    date = models.DateField("Дата публикации")
    body = StreamField(
        [
            ("heading", blocks.CharBlock(form_classname="full title")),
            ("paragraph", blocks.RichTextBlock(features=["bold","italic","link","ol","ul","hr"])),
        ],
        use_json_field=True,
    )

    content_panels = Page.content_panels + [
        FieldPanel("date"),
        FieldPanel("body"),
    ]

class GarageIndexPage(Page):
    intro = RichTextField(blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro")]

class GaragePostPage(Page):
    title2 = models.CharField(max_length=255, blank=True)
    body = StreamField(
        [("paragraph", blocks.RichTextBlock(features=["bold","italic","link","ol","ul"]))],
        use_json_field=True,
    )
    content_panels = Page.content_panels + [
        FieldPanel("title2"),
        FieldPanel("body"),
    ]

class CatalogIndexPage(Page):
    intro = RichTextField(blank=True)
    content_panels = Page.content_panels + [FieldPanel("intro")]

class CatalogItemPage(Page):
    price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = RichTextField(blank=True)
    content_panels = Page.content_panels + [
        FieldPanel("price"),
        FieldPanel("description"),
    ]
