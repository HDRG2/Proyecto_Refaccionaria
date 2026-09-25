using CommunityToolkit.Mvvm.ComponentModel;
using Refaccionaria.Backend.Repositories;

namespace Refaccionaria.Frontend.Models;

public partial class ModeloAuto : ObservableObject, IEntity
{
    [ObservableProperty]
    private int id;

    [ObservableProperty]
    private string marca = string.Empty;

    [ObservableProperty]
    private string modelo = string.Empty;

    [ObservableProperty]
    private int anioInicio;

    [ObservableProperty]
    private int anioFin;

    public string DescripcionCompleta => $"{Marca} {Modelo} ({AnioInicio}-{AnioFin})";
}