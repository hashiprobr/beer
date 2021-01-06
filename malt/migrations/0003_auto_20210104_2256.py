# Generated by Django 3.1.4 on 2021-01-04 22:56

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.db.models.expressions
import malt.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('malt', '0002_fileasset_folderasset'),
    ]

    operations = [
        migrations.CreateModel(
            name='Calendar',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=22)),
                ('active', models.BooleanField()),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=44)),
                ('begin_date', models.DateField()),
                ('end_date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='CalendarCancelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('title', models.CharField(max_length=44)),
            ],
        ),
        migrations.CreateModel(
            name='Course',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('slug', models.SlugField(max_length=22)),
                ('active', models.BooleanField()),
                ('timestamp', models.DateTimeField(auto_now=True)),
                ('title', models.CharField(max_length=44)),
            ],
        ),
        migrations.CreateModel(
            name='Schedule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=44)),
            ],
        ),
        migrations.CreateModel(
            name='ScheduleCancelation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField()),
                ('title', models.CharField(max_length=44)),
            ],
        ),
        migrations.CreateModel(
            name='SingleEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin_time', models.TimeField(null=True)),
                ('end_time', models.TimeField(null=True)),
                ('place', models.CharField(max_length=44, null=True)),
                ('date', models.DateField()),
            ],
        ),
        migrations.CreateModel(
            name='WeeklyEvent',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('begin_time', models.TimeField(null=True)),
                ('end_time', models.TimeField(null=True)),
                ('place', models.CharField(max_length=44, null=True)),
                ('weekday', models.IntegerField(choices=[(0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'), (5, 'Saturday'), (6, 'Sunday')])),
            ],
        ),
        migrations.AlterField(
            model_name='fileasset',
            name='name',
            field=models.CharField(max_length=22, validators=[malt.models.validate_slash]),
        ),
        migrations.AlterField(
            model_name='folderasset',
            name='name',
            field=models.CharField(max_length=22, validators=[malt.models.validate_slash]),
        ),
        migrations.AlterUniqueTogether(
            name='fileasset',
            unique_together=set(),
        ),
        migrations.AlterUniqueTogether(
            name='folderasset',
            unique_together=set(),
        ),
        migrations.AddConstraint(
            model_name='fileasset',
            constraint=models.UniqueConstraint(fields=('user', 'parent', 'name'), name='fileasset_unique'),
        ),
        migrations.AddConstraint(
            model_name='folderasset',
            constraint=models.UniqueConstraint(fields=('user', 'parent', 'name'), name='folderasset_unique'),
        ),
        migrations.AddField(
            model_name='weeklyevent',
            name='schedule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='malt.schedule'),
        ),
        migrations.AddField(
            model_name='singleevent',
            name='schedule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='malt.schedule'),
        ),
        migrations.AddField(
            model_name='schedulecancelation',
            name='schedule',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='malt.schedule'),
        ),
        migrations.AddField(
            model_name='schedule',
            name='course',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='malt.course'),
        ),
        migrations.AddField(
            model_name='course',
            name='calendar',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='malt.calendar'),
        ),
        migrations.AddField(
            model_name='calendarcancelation',
            name='calendar',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='malt.calendar'),
        ),
        migrations.AddField(
            model_name='calendar',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddConstraint(
            model_name='weeklyevent',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('begin_time__isnull', True), ('end_time__isnull', True)), models.Q(('begin_time__isnull', False), ('begin_time__lt', django.db.models.expressions.F('end_time')), ('end_time__isnull', False)), _connector='OR'), name='weeklyevent_times_order'),
        ),
        migrations.AddConstraint(
            model_name='singleevent',
            constraint=models.CheckConstraint(check=models.Q(models.Q(('begin_time__isnull', True), ('end_time__isnull', True)), models.Q(('begin_time__isnull', False), ('begin_time__lt', django.db.models.expressions.F('end_time')), ('end_time__isnull', False)), _connector='OR'), name='singleevent_times_order'),
        ),
        migrations.AddConstraint(
            model_name='schedulecancelation',
            constraint=models.UniqueConstraint(fields=('schedule', 'date'), name='schedulecancelation_unique'),
        ),
        migrations.AddConstraint(
            model_name='course',
            constraint=models.UniqueConstraint(fields=('calendar', 'slug', 'active'), name='course_unique'),
        ),
        migrations.AddConstraint(
            model_name='calendarcancelation',
            constraint=models.UniqueConstraint(fields=('calendar', 'date'), name='calendarcancelation_unique'),
        ),
        migrations.AddConstraint(
            model_name='calendar',
            constraint=models.UniqueConstraint(fields=('user', 'slug', 'active'), name='calendar_unique'),
        ),
        migrations.AddConstraint(
            model_name='calendar',
            constraint=models.CheckConstraint(check=models.Q(begin_date__lte=django.db.models.expressions.F('end_date')), name='calendar_dates_order'),
        ),
    ]