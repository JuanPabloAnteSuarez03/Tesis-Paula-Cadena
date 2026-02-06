import ifcopenshell

modelo = ifcopenshell.open("modelo.ifc")

print("MODELO IFC CARGADO")
print("====================")

# Tipos de elementos constructivos comunes
tipos_elementos = [
    "IfcWall",
    "IfcSlab",
    "IfcColumn",
    "IfcBeam",
    "IfcFooting",
    "IfcStair"
]

for tipo in tipos_elementos:
    elementos = modelo.by_type(tipo)

    if not elementos:
        continue  # si no hay de ese tipo, pasa al siguiente

    print(f"\nTIPO DE ELEMENTO: {tipo}")
    print("-------------------------")

    for elem in elementos:
        print("ID:", elem.GlobalId)
        print("Nombre:", elem.Name)

        tiene_cantidades = False

        for rel in elem.IsDefinedBy:
            if rel.is_a("IfcRelDefinesByProperties"):
                prop = rel.RelatingPropertyDefinition

                if prop.is_a("IfcElementQuantity"):
                    tiene_cantidades = True
                    for q in prop.Quantities:
                        valor = (
                            getattr(q, "LengthValue", None)
                            or getattr(q, "AreaValue", None)
                            or getattr(q, "VolumeValue", None)
                        )
                        print(f"  {q.Name}: {valor}")

        if not tiene_cantidades:
            print("  (Sin cantidades)")

        print("-------------------------")
