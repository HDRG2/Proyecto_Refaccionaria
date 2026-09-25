using System;
using System.Collections.Generic;
using System.Collections.ObjectModel;
using System.Linq;
using System.Threading.Tasks;
using CommunityToolkit.Mvvm.ComponentModel;
using CommunityToolkit.Mvvm.Input;
using Refaccionaria.Backend.Repositories;
using Refaccionaria.Frontend.Models;

namespace Refaccionaria.Frontend.ViewModels;

// Una línea dentro del carrito de venta (no se guarda tal cual, es temporal en memoria)
public partial class ItemVenta : ObservableObject
{
    public Refaccion Pieza { get; }

    [ObservableProperty]
    private int cantidad;

    public ItemVenta(Refaccion pieza, int cantidad)
    {
        Pieza = pieza;
        this.cantidad = cantidad;
    }

    public decimal Subtotal => Pieza.Precio * Cantidad;

    partial void OnCantidadChanged(int value) => OnPropertyChanged(nameof(Subtotal));
}

public partial class VentaViewModel : ObservableObject
{
    private readonly JsonRepository<Refaccion> _refaccionesRepo;
    private readonly JsonRepository<Categoria> _categoriasRepo;
    private readonly JsonRepository<Marca> _marcasRepo;
    private readonly JsonRepository<Venta> _ventasRepo;
    private readonly JsonRepository<DetalleVenta> _detalleVentaRepo;

    private List<Categoria> _categoriasCatalogo = new();
    private List<Marca> _marcasCatalogo = new();

    public ObservableCollection<Refaccion> Catalogo { get; } = new();
    public ObservableCollection<ItemVenta> Carrito { get; } = new();

    [ObservableProperty]
    private string textoBusqueda = string.Empty;

    [ObservableProperty]
    private decimal total;

    public string TotalTexto => Total.ToString("C0", new System.Globalization.CultureInfo("es-MX"));

    partial void OnTotalChanged(decimal value) => OnPropertyChanged(nameof(TotalTexto));
    partial void OnTextoBusquedaChanged(string value) => FiltrarCatalogo();

    private List<Refaccion> _todasLasPiezas = new();

    public VentaViewModel()
    {
        var carpetaData = System.IO.Path.Combine(AppContext.BaseDirectory, "Data");
        _refaccionesRepo = new JsonRepository<Refaccion>(System.IO.Path.Combine(carpetaData, "refacciones.json"));
        _categoriasRepo = new JsonRepository<Categoria>(System.IO.Path.Combine(carpetaData, "categorias.json"));
        _marcasRepo = new JsonRepository<Marca>(System.IO.Path.Combine(carpetaData, "marcas.json"));
        _ventasRepo = new JsonRepository<Venta>(System.IO.Path.Combine(carpetaData, "ventas.json"));
        _detalleVentaRepo = new JsonRepository<DetalleVenta>(System.IO.Path.Combine(carpetaData, "detalle_ventas.json"));
    }

    public async Task InitializeAsync()
    {
        _categoriasCatalogo = (await _categoriasRepo.GetAllAsync()).ToList();
        _marcasCatalogo = (await _marcasRepo.GetAllAsync()).ToList();

        _todasLasPiezas = (await _refaccionesRepo.GetAllAsync()).ToList();
        foreach (var r in _todasLasPiezas)
        {
            r.MarcaNombre = _marcasCatalogo.FirstOrDefault(m => m.Id == r.MarcaId)?.Nombre ?? string.Empty;
            r.CategoriaNombre = _categoriasCatalogo.FirstOrDefault(c => c.Id == r.CategoriaId)?.Nombre ?? string.Empty;
        }

        FiltrarCatalogo();
    }

    private void FiltrarCatalogo()
    {
        var texto = TextoBusqueda.Trim().ToLowerInvariant();
        var lista = string.IsNullOrEmpty(texto)
            ? _todasLasPiezas
            : _todasLasPiezas.Where(r =>
                $"{r.Codigo} {r.Nombre} {r.MarcaNombre}".ToLowerInvariant().Contains(texto));

        Catalogo.Clear();
        foreach (var r in lista) Catalogo.Add(r);
    }

    [RelayCommand]
    private void AgregarAlCarrito(Refaccion pieza)
    {
        if (pieza is null) return;

        var existente = Carrito.FirstOrDefault(i => i.Pieza.Id == pieza.Id);
        if (existente is not null)
        {
            if (existente.Cantidad < pieza.Stock)
                existente.Cantidad++;
        }
        else if (pieza.Stock > 0)
        {
            Carrito.Add(new ItemVenta(pieza, 1));
        }

        ActualizarTotal();
    }

    [RelayCommand]
    private void QuitarDelCarrito(ItemVenta item)
    {
        if (item is null) return;
        Carrito.Remove(item);
        ActualizarTotal();
    }

    private void ActualizarTotal() => Total = Carrito.Sum(i => i.Subtotal);

    [RelayCommand]
    private async Task ConfirmarVentaAsync()
    {
        if (Carrito.Count == 0) return;

        var venta = new Venta
        {
            Fecha = DateTime.Now,
            Total = Total,
            UsuarioId = 0
        };
        await _ventasRepo.AddAsync(venta);

        foreach (var item in Carrito)
        {
            var detalle = new DetalleVenta
            {
                VentaId = venta.Id,
                RefaccionId = item.Pieza.Id,
                Cantidad = item.Cantidad,
                PrecioUnitario = item.Pieza.Precio
            };
            await _detalleVentaRepo.AddAsync(detalle);

            item.Pieza.Stock -= item.Cantidad;
            await _refaccionesRepo.UpdateAsync(item.Pieza);
        }

        Carrito.Clear();
        Total = 0;
    }
}