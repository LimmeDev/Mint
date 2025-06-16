using Mafi;
using Mafi.Core.Mods;
using Mafi.Core.Game;
using Mafi.Core.Entities.Static;
using Mafi.Core.Prototypes;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using Mafi.Core.Entities;
using Mafi.Collections;
using Mafi.Core.Products;
using Mafi.Core.Time;
using Mafi.Core.Mods.Attributes;
using Mafi.Core.GameLoop;

namespace CoI_AI_Mod
{
	public sealed class CoI_AI_Mod : IMod
	{
		public string Name => "Captain of Industry AI Mod";
		public int Version => 1;
		public bool IsUiOnly => false;

		// New in COI 0.7+: every mod must expose a config object even if it is empty.
		// Replace `EmptyConfig` with your own ModConfig implementation once you need
		// user-visible settings inside the game's mod UI.
		public IModConfig ModConfig { get; } = new EmptyConfig();

		private IGameLoop _gameLoop;
		private ProtosDb _protosDb;
		private IEntitiesManager _entitiesManager;
		private static readonly HttpClient _httpClient = new HttpClient();
		private int _tickCounter = 0;
		private const int TickInterval = 120; // Approx 2 seconds
		private bool _isWaitingForResponse = false;
		private const string ServerUrl = "http://127.0.0.1:8000/";

		// Signature changed (added isEditor) in API 0.7+.
		public void Initialize(DependencyResolver resolver, bool isEditor)
		{
			_gameLoop = resolver.Resolve<IGameLoop>();
			_protosDb = resolver.Resolve<ProtosDb>();
			_entitiesManager = resolver.Resolve<IEntitiesManager>();
		}

		public void RegisterPrototypes(ProtoRegistrator registrator)
		{
			// We are not registering any new entities or products in this mod.
		}

		// Updated signature (added isEditor).
		public void RegisterDependencies(DependencyResolverBuilder depBuilder, ProtosDb protosDb, bool isEditor)
		{
			// No new dependencies needed.
		}
		
		// Back-compat overload kept so the code still compiles on older SDKs if someone targets them.
		#pragma warning disable CS0114
		public void RegisterDependencies(DependencyResolverBuilder depBuilder, ProtosDb protosDb)
			=> RegisterDependencies(depBuilder, protosDb, false);
		#pragma warning restore CS0114

		public void EarlyInit(DependencyResolver resolver)
		{
		   // Not needed for this mod.
		}

		public void LateInit(DependencyResolver resolver)
		{
			_gameLoop.UpdateEv.Add(this.OnUpdate);
			Log.Info("AI Mod Initialized, starting update loop.");
		}

		private async void OnUpdate(GameTime gameTime)
		{
			if (_isWaitingForResponse) return;

			_tickCounter++;
			if (_tickCounter < TickInterval) return;
			
			_tickCounter = 0;
			_isWaitingForResponse = true;

			try
			{
				// 1. Gather game data
				var worldData = new WorldData();

				// Get all products and their stored quantities
				var allProducts = _protosDb.Filter<ProductProto>(p => !p.IsVirtual);
				foreach (ProductProto product in allProducts)
				{
					Quantity quantity = _entitiesManager.CountProducts(product);
					if (quantity > 0)
					{
						worldData.Products.Add(product.Id.ToString(), quantity.ToString());
					}
				}

				// 2. Serialize to JSON
				var options = new JsonSerializerOptions { WriteIndented = true };
				string jsonPayload = JsonSerializer.Serialize(worldData, options);

				// 3. Send data to Python server
				var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");
				
				Log.Info("Sending data to AI Brain...");
				var response = await _httpClient.PostAsync(ServerUrl, content);

				if (response.IsSuccessStatusCode)
				{
					string responseBody = await response.Content.ReadAsStringAsync();
					var aiResponse = JsonSerializer.Deserialize<AiResponse>(responseBody);
					if (aiResponse != null && !string.IsNullOrEmpty(aiResponse.message))
					{
						Log.Info($"[AI BRAIN]: {aiResponse.message}");
					}
				}
				else
				{
					Log.Warning($"Failed to connect to AI Brain. Status: {response.StatusCode}");
				}
			}
			catch (HttpRequestException e)
			{
				Log.Error($"Connection error with AI Brain: {e.Message}. Is the Python server running?");
			}
			catch (System.Exception e)
			{
				Log.Error($"An error occurred during the update loop: {e.Message}");
			}
			finally
			{
				_isWaitingForResponse = false;
			}
		}
	}

	// Data structure for sending to Python
	public class WorldData
	{
		public Dictionary<string, string> Products { get; set; } = new Dictionary<string, string>();
	}

	// Data structure for receiving from Python
	public class AiResponse
	{
		public string message { get; set; }
	}
}