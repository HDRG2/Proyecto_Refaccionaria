using CommunityToolkit.Mvvm.ComponentModel;
using Refaccionaria.Backend.Repositories;
using System.Text.Json.Serialization;

namespace Refaccionaria.Frontend.Models;

public partial class DetalleVenta : ObservableObject, IEntity
{
    [ObservableProperty]
    private int id;

    [ObservableProperty]
    private int ventaId;

    [ObservableProperty]
    private int refaccionId;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(Subtotal))]
    [NotifyPropertyChangedFor(nameof(ImporteTexto))]
    private int cantidad;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(Subtotal))]
    [NotifyPropertyChangedFor(nameof(PrecioUnitarioTexto))]
    [NotifyPropertyChangedFor(nameof(ImporteTexto))]
    private decimal precioUnitario;

    [ObservableProperty]
    private Refaccion? refaccion;


    // =========================================================
    // SUBTOTAL
    // =========================================================

    public decimal Subtotal =>
        Cantidad * PrecioUnitario;


    // =========================================================
    // PROPIEDADES PARA MOSTRAR EN LA INTERFAZ
    // =========================================================

    [JsonIgnore]
    public string PrecioUnitarioTexto =>
        $"{PrecioUnitario:C} c/u";


    [JsonIgnore]
    public string ImporteTexto =>
        Subtotal.ToString("C");
}