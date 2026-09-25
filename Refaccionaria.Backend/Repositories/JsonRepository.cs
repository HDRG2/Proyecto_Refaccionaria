using System.Text.Json;
using System.Threading;

namespace Refaccionaria.Backend.Repositories;

public class JsonRepository<T> : IRepository<T> where T : class, IEntity
{
    private readonly string _rutaArchivo;
    private List<T> _items = new();
    private bool _cargado = false;
    private readonly SemaphoreSlim _lock = new(1, 1);

    public JsonRepository(string rutaArchivo)
    {
        _rutaArchivo = rutaArchivo;
    }

    private async Task AsegurarCargadoAsync()
    {
        if (_cargado) return;

        await _lock.WaitAsync();
        try
        {
            if (_cargado) return;

            if (File.Exists(_rutaArchivo))
            {
                string json = await File.ReadAllTextAsync(_rutaArchivo);
                _items = JsonSerializer.Deserialize<List<T>>(json) ?? new List<T>();
            }
            else
            {
                _items = new List<T>();
            }

            _cargado = true;
        }
        finally
        {
            _lock.Release();
        }
    }

    private async Task GuardarAsync()
    {
        var opciones = new JsonSerializerOptions { WriteIndented = true };
        string json = JsonSerializer.Serialize(_items, opciones);
        await File.WriteAllTextAsync(_rutaArchivo, json);
    }

    public async Task<IEnumerable<T>> GetAllAsync()
    {
        await AsegurarCargadoAsync();
        return _items;
    }

    public async Task<T?> GetByIdAsync(int id)
    {
        await AsegurarCargadoAsync();
        return _items.FirstOrDefault(x => x.Id == id);
    }

    public async Task AddAsync(T entity)
    {
        await AsegurarCargadoAsync();
        entity.Id = _items.Count > 0 ? _items.Max(x => x.Id) + 1 : 1;
        _items.Add(entity);
        await GuardarAsync();
    }

    public async Task UpdateAsync(T entity)
    {
        await AsegurarCargadoAsync();
        var index = _items.FindIndex(x => x.Id == entity.Id);
        if (index == -1) return;
        _items[index] = entity;
        await GuardarAsync();
    }

    public async Task DeleteAsync(int id)
    {
        await AsegurarCargadoAsync();
        _items.RemoveAll(x => x.Id == id);
        await GuardarAsync();
    }
}