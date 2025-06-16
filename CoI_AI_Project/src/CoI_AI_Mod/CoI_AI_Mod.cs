using Mafi;
using Mafi.Core.Mods;
using Mafi.Core.Entities.Static;
using Mafi.Core.Prototypes;
using System.Collections.Generic;
using System.Net.Http;
using System.Text;
using System.Text.Json;
using Mafi.Core.Entities;
using Mafi.Core.Products;

namespace CoI_AI_Mod
{
	public sealed class CoI_AI_Mod : IMod
	{
		public string Name => "Captain of Industry AI Mod";
		public int Version => 1;
		public bool IsUiOnly => false;

		// ModConfig is only required in COI 0.7+. The 0.6 API we target does not define it, so we omit it here.

		private ProtosDb _protosDb;
		private IEntitiesManager _entitiesManager;
		private static readonly HttpClient _httpClient = new HttpClient();
		private const string ServerUrl = "http://127.0.0.1:8000/";

		// Signature changed (added isEditor) in API 0.7+.
		public void Initialize(DependencyResolver resolver, bool isEditor)
		{
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
			Log.Info("AI Mod Initialized (0.6 build). No automatic tick polling available – call SendWorldSnapshotToAiServer() from another mod hook if needed.");
		}

		/// <summary>
		/// Collects a lightweight snapshot of the current world and POSTs it to the Python AI service.
		/// In COI 0.6 this is NOT called automatically – invoke manually from another event or console command.
		/// </summary>
		public async System.Threading.Tasks.Task SendWorldSnapshotToAiServer()
		{
			// 1. Gather game data
			var worldData = new WorldData();

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

			try
			{
				var content = new StringContent(jsonPayload, Encoding.UTF8, "application/json");
				Log.Info("[AI] Posting world snapshot…");
				var response = await _httpClient.PostAsync(ServerUrl, content);

				if (response.IsSuccessStatusCode)
				{
					string responseBody = await response.Content.ReadAsStringAsync();
					var aiResponse = JsonSerializer.Deserialize<AiResponse>(responseBody);
					if (aiResponse != null && !string.IsNullOrEmpty(aiResponse.message))
					{
						Log.Info($"[AI] {aiResponse.message}");
					}
				}
				else
				{
					Log.Warning($"[AI] HTTP {response.StatusCode} while sending snapshot.");
				}
			}
			catch (HttpRequestException e)
			{
				Log.Error($"[AI] Connection error: {e.Message}");
			}
			catch (System.Exception e)
			{
				Log.Error($"[AI] Unexpected error: {e.Message}");
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