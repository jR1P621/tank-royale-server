using Robocode.TankRoyale.BotApi;
using Robocode.TankRoyale.BotApi.Graphics;
using Microsoft.ML.OnnxRuntime;
using Microsoft.ML.OnnxRuntime.Tensors;
using System;
using System.Collections.Generic;
using System.IO;
using System.Text.Json;

public class BulletInfo
{
    public double X { get; set; }
    public double Y { get; set; }
    public double Direction { get; set; }
    public double Power { get; set; }
    public bool IsEnemy { get; set; }
    public int Tick { get; set; }
}

public class NeuralBot : Bot
{
    private InferenceSession session;
    private List<BulletInfo> activeBullets = new();
    private float[] lastEnemyData = new float[5]; // x, y, dir, energy, distance

    public NeuralBot()
    {
        var botInfo = BotInfo.FromFile("NeuralBot.json");
        session = new InferenceSession("model.onnx");
    }

    public override void Run()
    {
        // Load colors
        var colorsJson = File.ReadAllText("colors.json");
        var colors = JsonSerializer.Deserialize<Dictionary<string, int[]>>(colorsJson);
        BodyColor = Color.FromRgb(colors["bodyColor"][0], colors["bodyColor"][1], colors["bodyColor"][2]);
        TurretColor = Color.FromRgb(colors["turretColor"][0], colors["turretColor"][1], colors["turretColor"][2]);
        RadarColor = Color.FromRgb(colors["radarColor"][0], colors["radarColor"][1], colors["radarColor"][2]);
        BulletColor = Color.FromRgb(colors["bulletColor"][0], colors["bulletColor"][1], colors["bulletColor"][2]);
        ScanColor = Color.FromRgb(colors["scanColor"][0], colors["scanColor"][1], colors["scanColor"][2]);

        while (IsRunning)
        {
            // Get current state
            var state = GetStateVector();

            // Infer actions
            var actions = InferActions(state);

            // Execute actions
            ExecuteActions(actions);

            // Scan
            SetTurnRadarRight(360);
            Go();
        }
    }

    private float[] GetStateVector()
    {
        // Normalize inputs
        float normX = (float)X / ArenaWidth;
        float normY = (float)Y / ArenaHeight;
        float normDir = (float)Direction / 360f;
        float normEnergy = (float)Energy / 100f;
        float normGunHeat = GunHeat / 3f;
        float normGunDir = (float)GunDirection / 360f;
        float normRadarDir = (float)RadarDirection / 360f;
        float normArenaW = 1f;
        float normArenaH = 1f;
        float normEnemyX = lastEnemyData[0] / ArenaWidth;
        float normEnemyY = lastEnemyData[1] / ArenaHeight;
        float normEnemyDir = lastEnemyData[2] / 360f;
        float normEnemyEnergy = lastEnemyData[3] / 100f;
        float normDistance = lastEnemyData[4] / Math.Max(ArenaWidth, ArenaHeight);

        var state = new List<float> { normX, normY, normDir, normEnergy, normGunHeat, normGunDir, normRadarDir, normArenaW, normArenaH, normEnemyX, normEnemyY, normEnemyDir, normEnemyEnergy, normDistance };

        // Add up to 5 closest bullets
        var enemyBullets = activeBullets.Where(b => b.IsEnemy).ToList();
        var sortedBullets = enemyBullets.OrderBy(b => DistanceTo(b.X, b.Y)).Take(5);
        foreach (var bullet in sortedBullets)
        {
            float relAngle = (float)((Math.Atan2(bullet.Y - Y, bullet.X - X) * 180 / Math.PI - Direction + 360) % 360) / 360f;
            float dist = (float)DistanceTo(bullet.X, bullet.Y) / Math.Max(ArenaWidth, ArenaHeight);
            float isEnemy = bullet.IsEnemy ? 1f : 0f;
            state.Add(relAngle);
            state.Add(dist);
            state.Add(isEnemy);
        }
        // Pad to 5 bullets
        while (state.Count < 12 + 15) state.Add(0f);

        return state.ToArray();
    }

    private float[] InferActions(float[] state)
    {
        var inputTensor = new DenseTensor<float>(state, new int[] { 1, 12 });
        var inputs = new List<NamedOnnxValue> { NamedOnnxValue.CreateFromTensor("input", inputTensor) };
        using var results = session.Run(inputs);
        var outputTensor = results.First().AsTensor<float>();
        return outputTensor.ToArray(); // 4 values: body_turn, move_dist, gun_turn, fire_power
    }

    private void ExecuteActions(float[] actions)
    {
        float bodyTurn = actions[0] * 180f; // -180 to 180
        float moveDist = actions[1] * 100f; // -100 to 100
        float gunTurn = actions[2] * 180f; // -180 to 180
        float firePower = Math.Clamp(actions[3] * 3f, 0f, 3f); // 0 to 3

        SetTurnLeft(bodyTurn);
        if (moveDist > 0)
            Forward(moveDist);
        else
            Back(-moveDist);
        SetTurnGunLeft(gunTurn);
        if (firePower > 0 && GunHeat == 0)
            Fire(firePower);
    }

    public override void OnScannedBot(ScannedBotEvent evt)
    {
        lastEnemyData[0] = (float)evt.X;
        lastEnemyData[1] = (float)evt.Y;
        lastEnemyData[2] = (float)evt.Direction;
        lastEnemyData[3] = (float)evt.Energy;
        lastEnemyData[4] = (float)DistanceTo(evt.X, evt.Y);
    }

    public override void OnBulletFired(BulletFiredEvent evt)
    {
        activeBullets.Add(new BulletInfo
        {
            X = evt.Bullet.X,
            Y = evt.Bullet.Y,
            Direction = evt.Bullet.Direction,
            Power = evt.Bullet.Power,
            IsEnemy = evt.Bullet.OwnerId != Id,
            Tick = Time
        });
    }

    public override void OnBulletHit(BulletHitEvent evt)
    {
        activeBullets.RemoveAll(b => b.X == evt.Bullet.X && b.Y == evt.Bullet.Y);
    }

    public override void OnBulletHitBullet(BulletHitBulletEvent evt)
    {
        activeBullets.RemoveAll(b => b.X == evt.Bullet.X && b.Y == evt.Bullet.Y);
        activeBullets.RemoveAll(b => b.X == evt.HitBullet.X && b.Y == evt.HitBullet.Y);
    }

    public override void OnHitByBullet(HitByBulletEvent evt)
    {
        // Optional: adjust behavior
    }

    public override void OnHitWall(HitWallEvent evt)
    {
        // Optional: adjust behavior
    }
}

class Program
{
    static void Main() => new NeuralBot().Run();
}