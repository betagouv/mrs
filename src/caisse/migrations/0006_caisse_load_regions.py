# Generated by Django 2.1.9 on 2019-06-27 14:09

import os
from django.db import migrations

regions_list = [
    {
        "fields": {
            "cheflieu_code": "69123",
            "insee_id": "84",
            "name": "Auvergne-Rhône-Alpes"
        },
        "model": "caisse.region",
        "pk": 1
    },
    {
        "fields": {
            "cheflieu_code": "21231",
            "insee_id": "27",
            "name": "Bourgogne-Franche-Comté"
        },
        "model": "caisse.region",
        "pk": 2
    },
    {
        "fields": {
            "cheflieu_code": "35238",
            "insee_id": "53",
            "name": "Bretagne"
        },
        "model": "caisse.region",
        "pk": 3
    },
    {
        "fields": {
            "cheflieu_code": "45234",
            "insee_id": "24",
            "name": "Centre-Val de Loire"
        },
        "model": "caisse.region",
        "pk": 4
    },
    {
        "fields": {
            "cheflieu_code": "2A004",
            "insee_id": "94",
            "name": "Corse"
        },
        "model": "caisse.region",
        "pk": 5
    },
    {
        "fields": {
            "cheflieu_code": "67482",
            "insee_id": "44",
            "name": "Grand Est"
        },
        "model": "caisse.region",
        "pk": 6
    },
    {
        "fields": {
            "cheflieu_code": "97105",
            "insee_id": "01",
            "name": "Guadeloupe"
        },
        "model": "caisse.region",
        "pk": 7
    },
    {
        "fields": {
            "cheflieu_code": "97302",
            "insee_id": "03",
            "name": "Guyane"
        },
        "model": "caisse.region",
        "pk": 8
    },
    {
        "fields": {
            "cheflieu_code": "59350",
            "insee_id": "32",
            "name": "Hauts-de-France"
        },
        "model": "caisse.region",
        "pk": 9
    },
    {
        "fields": {
            "cheflieu_code": "75056",
            "insee_id": "11",
            "name": "Ile-de-France"
        },
        "model": "caisse.region",
        "pk": 10
    },
    {
        "fields": {
            "cheflieu_code": "97411",
            "insee_id": "04",
            "name": "La Réunion"
        },
        "model": "caisse.region",
        "pk": 11
    },
    {
        "fields": {
            "cheflieu_code": "97209",
            "insee_id": "02",
            "name": "Martinique"
        },
        "model": "caisse.region",
        "pk": 12
    },
    {
        "fields": {
            "cheflieu_code": "97608",
            "insee_id": "06",
            "name": "Mayotte"
        },
        "model": "caisse.region",
        "pk": 13
    },
    {
        "fields": {
            "cheflieu_code": "76540",
            "insee_id": "28",
            "name": "Normandie"
        },
        "model": "caisse.region",
        "pk": 14
    },
    {
        "fields": {
            "cheflieu_code": "33063",
            "insee_id": "75",
            "name": "Nouvelle-Aquitaine"
        },
        "model": "caisse.region",
        "pk": 15
    },
    {
        "fields": {
            "cheflieu_code": "31555",
            "insee_id": "76",
            "name": "Occitanie"
        },
        "model": "caisse.region",
        "pk": 16
    },
    {
        "fields": {
            "cheflieu_code": "44109",
            "insee_id": "52",
            "name": "Pays de la Loire"
        },
        "model": "caisse.region",
        "pk": 17
    },
    {
        "fields": {
            "cheflieu_code": "13055",
            "insee_id": "93",
            "name": "Provence-Alpes-Côte d'Azur"
        },
        "model": "caisse.region",
        "pk": 18
    },
    {
        "fields": {
            "cheflieu_code": "XXXXX",
            "insee_id": "XX",
            "name": "Régimes Spéciaux"
        },
        "model": "caisse.region",
        "pk": 19
    }
]


def insert_regions(apps, schema_editor):
    if 'CI' in os.environ:
        return
    Region = apps.get_model("caisse", "Region")
    db_alias = schema_editor.connection.alias
    Region.objects.using(db_alias).bulk_create([
        Region(**region_item["fields"])
        for region_item in regions_list
    ])


class Migration(migrations.Migration):

    dependencies = [
        ('caisse', '0005_caisse_ajout_regions'),
    ]

    operations = [

        migrations.RunPython(insert_regions)
    ]
