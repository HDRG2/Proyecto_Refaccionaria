using CommunityToolkit.Mvvm.ComponentModel;
using Refaccionaria.Backend.Repositories;
using System.Collections.ObjectModel;

namespace Refaccionaria.Frontend.Models;

public partial class Venta : ObservableObject, IEntity
{
    [ObservableProperty]
    private int id;

    [ObservableProperty]
    private string folio = string.Empty;

    [ObservableProperty]
    private DateTime fecha = DateTime.Now;

    [ObservableProperty]
    private int usuarioId;

    [ObservableProperty]
    private string metodoPago = string.Empty;

    [ObservableProperty]
    private string referencia = string.Empty;

    [ObservableProperty]
    private decimal recibido;

    [ObservableProperty]
    private decimal cambio;

    [ObservableProperty]
    private decimal total;

    [ObservableProperty]
    private ObservableCollection<DetalleVenta> lineas = new();
}