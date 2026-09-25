using CommunityToolkit.Mvvm.ComponentModel;
using Refaccionaria.Backend.Repositories;

namespace Refaccionaria.Frontend.Models;

public partial class Usuario : ObservableObject, IEntity
{
    [ObservableProperty]
    private int id;

    [ObservableProperty]
    private string nombreUsuario = string.Empty;

    [ObservableProperty]
    private string password = string.Empty;

    [ObservableProperty]
    private string rol = string.Empty; // "Administrador" o "Vendedor"

    [ObservableProperty] private string nombre = string.Empty;
    [ObservableProperty] private string telefono = string.Empty;
    [ObservableProperty] private bool activo = true;
}