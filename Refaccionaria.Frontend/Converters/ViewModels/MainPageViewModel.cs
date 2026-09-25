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

public partial class MainPageViewModel : ObservableObject
{
    private readonly JsonRepository<Refaccion> _refaccionesRepo;
    private readonly JsonRepository<Categoria> _categoriasRepo;
    private readonly JsonRepository<Marca> _marcasRepo;
    private readonly JsonRepository<ModeloAuto> _autosRepo;

    private List<Categoria> _categoriasCatalogo = new();

    public ObservableCollection<string> Categorias { get; } = new();
    public ObservableCollection<Categoria> CategoriasCatalogo { get; } = new();
    public ObservableCollection<Marca> MarcasCatalogo { get; } = new();
    public ObservableCollection<ModeloAuto> AutosCatalogo { get; } = new();

    public ObservableCollection<Refaccion> Refacciones { get; } = new();
    public ObservableCollection<Refaccion> Catalogo { get; } = new();

    public ObservableCollection<string> Marcas { get; } = new();
    public ObservableCollection<string> Modelos { get; } = new();

    public ObservableCollection<Refaccion> Alertas { get; } = new();

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(ResumenFiltros))]
    private string textoBusqueda = string.Empty;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(ResumenFiltros))]
    private string? marcaSeleccionada;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(ResumenFiltros))]
    private string? modeloSeleccionado;

    [ObservableProperty]
    [NotifyPropertyChangedFor(nameof(ResumenFiltros))]
    private string? categoriaSeleccionada;

    [ObservableProperty]
    private string orden = "nombre";

    [ObservableProperty] private int totalPiezas;
    [ObservableProperty] private int piezasEnExistencia;
    [ObservableProperty] private int piezasPorResurtir;
    [ObservableProperty] private int marcasCount;
    [ObservableProperty] private int autosCount;
    [ObservableProperty] private string valorInventarioTexto = "$0";

    public string ResumenFiltros
    {
        get
        {
            var partes = new List<string>();
            if (!string.IsNullOrEmpty(MarcaSeleccionada))
                partes.Add(string.IsNullOrEmpty(ModeloSeleccionado) ? MarcaSeleccionada : $"{MarcaSeleccionada} {ModeloSeleccionado}");
            if (!string.IsNullOrEmpty(CategoriaSeleccionada))
                partes.Add(CategoriaSeleccionada.ToLowerInvariant());
            if (!string.IsNullOrWhiteSpace(TextoBusqueda))
                partes.Add($"\u201c{TextoBusqueda.Trim()}\u201d");

            return partes.Count == 0
                ? "Mostrando todo el inventario."
                : $"{Catalogo.Count} {(Catalogo.Count == 1 ? "pieza" : "piezas")} para {string.Join(" · ", partes)}.";
        }
    }

    public MainPageViewModel()
    {
        var carpetaData = System.IO.Path.Combine(AppContext.BaseDirectory, "Data");
        _refaccionesRepo = new JsonRepository<Refaccion>(System.IO.Path.Combine(carpetaData, "refacciones.json"));
        _categoriasRepo = new JsonRepository<Categoria>(System.IO.Path.Combine(carpetaData, "categorias.json"));
        _marcasRepo = new JsonRepository<Marca>(System.IO.Path.Combine(carpetaData, "marcas.json"));
        _autosRepo = new JsonRepository<ModeloAuto>(System.IO.Path.Combine(carpetaData, "autos.json"));
    }

    public async Task InitializeAsync()
    {
        await CargarCatalogosAsync();
        await CargarRefaccionesAsync();
        ActualizarTodo();
    }

    private async Task CargarCatalogosAsync()
    {
        _categoriasCatalogo = (await _categoriasRepo.GetAllAsync()).ToList();
        Categorias.Clear();
        CategoriasCatalogo.Clear();
        foreach (var c in _categoriasCatalogo)
        {
            Categorias.Add(c.Nombre);
            CategoriasCatalogo.Add(c);
        }

        MarcasCatalogo.Clear();
        foreach (var m in await _marcasRepo.GetAllAsync()) MarcasCatalogo.Add(m);

        AutosCatalogo.Clear();
        foreach (var a in await _autosRepo.GetAllAsync()) AutosCatalogo.Add(a);
    }

    private async Task CargarRefaccionesAsync()
    {
        Refacciones.Clear();
        foreach (var r in await _refaccionesRepo.GetAllAsync())
        {
            ActualizarNombresDeCatalogo(r);
            Refacciones.Add(r);
        }
    }

    private string NombreMarca(int marcaId) =>
        MarcasCatalogo.FirstOrDefault(m => m.Id == marcaId)?.Nombre ?? string.Empty;

    private string NombreCategoria(int categoriaId) =>
        _categoriasCatalogo.FirstOrDefault(c => c.Id == categoriaId)?.Nombre ?? string.Empty;

    private ModeloAuto? AutoPorId(int autoId) =>
        AutosCatalogo.FirstOrDefault(a => a.Id == autoId);

    private void ActualizarNombresDeCatalogo(Refaccion r)
    {
        r.CategoriaNombre = NombreCategoria(r.CategoriaId);
        r.MarcaNombre = NombreMarca(r.MarcaId);
        r.AutosDescripciones = new ObservableCollection<string>(
            r.AutosCompatibles.Select(AutoPorId).Where(a => a is not null).Select(a => a!.DescripcionCompleta));
    }

    partial void OnTextoBusquedaChanged(string value) => FiltrarCatalogo();
    partial void OnCategoriaSeleccionadaChanged(string? value) => FiltrarCatalogo();
    partial void OnOrdenChanged(string value) => FiltrarCatalogo();

    partial void OnMarcaSeleccionadaChanged(string? value)
    {
        ModeloSeleccionado = null;
        ActualizarModelos();
        FiltrarCatalogo();
    }

    partial void OnModeloSeleccionadoChanged(string? value) => FiltrarCatalogo();

    [RelayCommand]
    private void SeleccionarCategoria(string? categoria)
    {
        if (!string.IsNullOrEmpty(categoria))
            CategoriaSeleccionada = CategoriaSeleccionada == categoria ? null : categoria;
    }

    [RelayCommand]
    private void LimpiarFiltros()
    {
        TextoBusqueda = string.Empty;
        MarcaSeleccionada = null;
        ModeloSeleccionado = null;
        CategoriaSeleccionada = null;
    }

    [RelayCommand]
    private void IrAAlerta(Refaccion pieza)
    {
        LimpiarFiltros();
        TextoBusqueda = pieza.Codigo;
    }

    public async Task<(bool exito, string? error)> GuardarPiezaAsync(Refaccion datos, int? editandoId)
    {
        if (datos.AutosCompatibles.Count == 0 && !datos.EsUniversal)
            return (false, "Anota al menos un auto compatible, o marca la pieza como universal.");

        var duplicada = Refacciones.Any(r => r.Codigo == datos.Codigo && r.Id != editandoId);
        if (duplicada)
            return (false, $"El código {datos.Codigo} ya está ocupado por otra pieza. Usa uno distinto.");

        if (editandoId is null)
        {
            ActualizarNombresDeCatalogo(datos);
            await _refaccionesRepo.AddAsync(datos);
            Refacciones.Add(datos);
        }
        else
        {
            var existente = Refacciones.First(r => r.Id == editandoId);
            existente.Codigo = datos.Codigo;
            existente.Nombre = datos.Nombre;
            existente.CategoriaId = datos.CategoriaId;
            existente.MarcaId = datos.MarcaId;
            existente.Precio = datos.Precio;
            existente.Stock = datos.Stock;
            existente.EsUniversal = datos.EsUniversal;
            existente.AutosCompatibles = datos.AutosCompatibles;
            ActualizarNombresDeCatalogo(existente);
            await _refaccionesRepo.UpdateAsync(existente);
        }

        ActualizarTodo();
        return (true, null);
    }

    [RelayCommand]
    private async Task EliminarPiezaAsync(Refaccion pieza)
    {
        Refacciones.Remove(pieza);
        await _refaccionesRepo.DeleteAsync(pieza.Id);
        ActualizarTodo();
    }

    private void ActualizarTodo()
    {
        ActualizarMarcas();
        ActualizarModelos();
        FiltrarCatalogo();
        ActualizarAlertasYEstadisticas();
    }

    private void ActualizarMarcas()
    {
        var marcas = Refacciones
            .Where(r => !r.EsUniversal)
            .SelectMany(r => r.AutosCompatibles)
            .Select(AutoPorId)
            .Where(a => a is not null)
            .Select(a => a!.Marca)
            .Distinct()
            .OrderBy(m => m, StringComparer.Create(new System.Globalization.CultureInfo("es-MX"), false));

        Marcas.Clear();
        foreach (var m in marcas) Marcas.Add(m);
    }

    private void ActualizarModelos()
    {
        Modelos.Clear();
        if (string.IsNullOrEmpty(MarcaSeleccionada)) return;

        var modelos = Refacciones
            .Where(r => !r.EsUniversal)
            .SelectMany(r => r.AutosCompatibles)
            .Select(AutoPorId)
            .Where(a => a is not null && a.Marca == MarcaSeleccionada)
            .Select(a => a!.Modelo)
            .Distinct()
            .OrderBy(m => m, StringComparer.Create(new System.Globalization.CultureInfo("es-MX"), false));

        foreach (var m in modelos) Modelos.Add(m);
    }

    private void FiltrarCatalogo()
    {
        var texto = TextoBusqueda.Trim().ToLowerInvariant();

        IEnumerable<Refaccion> lista = Refacciones.Where(r =>
        {
            var cajon = $"{r.Codigo} {r.Nombre} {r.MarcaNombre} {r.CategoriaNombre} {string.Join(' ', r.AutosDescripciones)}".ToLowerInvariant();

            var pasaTexto = string.IsNullOrEmpty(texto) || cajon.Contains(texto);
            var pasaCategoria = string.IsNullOrEmpty(CategoriaSeleccionada) || r.CategoriaNombre == CategoriaSeleccionada;
            var pasaMarca = string.IsNullOrEmpty(MarcaSeleccionada)
                || r.EsUniversal
                || r.AutosCompatibles.Select(AutoPorId).Any(a => a is not null && a.Marca == MarcaSeleccionada);
            var pasaModelo = string.IsNullOrEmpty(ModeloSeleccionado)
                || r.EsUniversal
                || r.AutosCompatibles.Select(AutoPorId).Any(a => a is not null && a.Modelo == ModeloSeleccionado);
            return pasaTexto && pasaCategoria && pasaMarca && pasaModelo;
        });

        lista = Orden switch
        {
            "nombre-desc" => lista.OrderByDescending(r => r.Nombre, StringComparer.Create(new System.Globalization.CultureInfo("es-MX"), false)),
            "precio-asc" => lista.OrderBy(r => r.Precio),
            "precio-desc" => lista.OrderByDescending(r => r.Precio),
            "stock-asc" => lista.OrderBy(r => r.Stock),
            _ => lista.OrderBy(r => r.Nombre, StringComparer.Create(new System.Globalization.CultureInfo("es-MX"), false)),
        };

        Catalogo.Clear();
        foreach (var r in lista) Catalogo.Add(r);
        OnPropertyChanged(nameof(ResumenFiltros));
    }

    private void ActualizarAlertasYEstadisticas()
    {
        var bajos = Refacciones.Where(r => r.StockBajo).OrderBy(r => r.Stock);
        Alertas.Clear();
        foreach (var r in bajos) Alertas.Add(r);

        TotalPiezas = Refacciones.Count;
        PiezasEnExistencia = Refacciones.Sum(r => r.Stock);
        PiezasPorResurtir = Alertas.Count;
        MarcasCount = Refacciones.Select(r => r.MarcaId).Distinct().Count();
        AutosCount = Refacciones
            .Where(r => !r.EsUniversal)
            .SelectMany(r => r.AutosCompatibles)
            .Select(AutoPorId)
            .Where(a => a is not null)
            .Select(a => a!.Id)
            .Distinct()
            .Count();
        var valor = Refacciones.Sum(r => r.Precio * r.Stock);
        ValorInventarioTexto = valor.ToString("C0", new System.Globalization.CultureInfo("es-MX"));
    }
}

