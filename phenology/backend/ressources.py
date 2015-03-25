from import_export import resources
from backend import models


class AreaResource(resources.ModelResource):

    class Meta:
        model = models.Area
        exclude = ('species', 'codezone', )


class SpeciesResource(resources.ModelResource):

    class Meta:
        model = models.Species


class SnowingResource(resources.ModelResource):

    class Meta:
        model = models.Snowing


class ObserverResource(resources.ModelResource):

    class Meta:
        model = models.Observer
        fields = (
            "id",
            "user",
            "user__username",
            'user__first_name',
            'user__last_name',
            'user__email',
            "city",
            "fonction",
            "adresse",
            "codepostal",
            "nationality",
            "organism",
            "category",
            "phone",
            "mobile",
            "is_crea",
            "is_active",
            "areas",
            "date_inscription",
        )
        export_order = fields