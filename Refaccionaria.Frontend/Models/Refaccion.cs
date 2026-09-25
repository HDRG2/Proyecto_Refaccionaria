using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Text.Json.Serialization;

using CommunityToolkit.Mvvm.ComponentModel;

using Refaccionaria.Backend.Repositories;

namespace Refaccionaria.Frontend.Models;

public partial class Refaccion : ObservableObject, IEntity
{
    [ObservableProperty]
    private int id;

    [ObservableProperty]
    private string codigo = string.Empty;

    [ObservableProperty]
    private string nombre = string.Empty;

    [ObservableProperty]
    private int marcaId;

    [ObservableProperty]
    private int categoriaId;

    [ObservableProperty]
    private decimal precio;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(ExistenciaTexto))]
    private int stock;

    [ObservableProperty]
    private bool stockBajo;

    [ObservableProperty]
    private bool activo = true;

    [ObservableProperty]
    private bool esUniversal;

    [ObservableProperty]
    private List<int> autosCompatibles = new();

    [ObservableProperty]
    private string marcaNombre = string.Empty;

    [ObservableProperty]
    private string categoriaNombre = string.Empty;

    [ObservableProperty]
    private ObservableCollection<string> autosDescripciones = new();


    // =========================================================
    // PROPIEDADES SOLO PARA LA INTERFAZ
    // =========================================================

    [JsonIgnore]
    public string CompatibilidadTexto
    {
        get
        {
            if (EsUniversal)
            {
                return "Universal (todos los autos)";
            }

            if (AutosDescripciones.Count > 0)
            {
                return string.Join(
                    ", ",
                    AutosDescripciones
                );
            }

            return "Sin autos asignados";
        }
    }


    [JsonIgnore]
    public string ExistenciaTexto
    {
        get
        {
            return Stock == 1
                ? "1 en existencia"
                : $"{Stock} en existencia";
        }
    }


    [JsonIgnore]
    public string PrecioTexto
    {
        get
        {
            return Precio.ToString("C");
        }
    }
}
