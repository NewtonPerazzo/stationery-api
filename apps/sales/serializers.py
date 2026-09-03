from rest_framework import serializers

from .models import WeekdayCommissionRule


class WeekdayCommissionRuleSerializer(serializers.ModelSerializer):
    weekday_name = serializers.CharField(
        source='get_weekday_display',
        read_only=True,
    )

    class Meta:
        model = WeekdayCommissionRule
        fields = (
            'id',
            'weekday',
            'weekday_name',
            'minimum_percentage',
            'maximum_percentage',
            'created_at',
            'updated_at',
        )
        read_only_fields = ('id', 'weekday_name', 'created_at', 'updated_at')

    def validate(self, attrs):
        minimum = attrs.get(
            'minimum_percentage',
            getattr(self.instance, 'minimum_percentage', None),
        )
        maximum = attrs.get(
            'maximum_percentage',
            getattr(self.instance, 'maximum_percentage', None),
        )

        if minimum is not None and maximum is not None and minimum > maximum:
            raise serializers.ValidationError({
                'maximum_percentage': (
                    'O percentual máximo deve ser maior ou igual ao mínimo.'
                ),
            })

        return attrs
