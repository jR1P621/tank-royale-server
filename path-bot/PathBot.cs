#:package Robocode.TankRoyale.BotApi@0.34.1

using System;
using System.Collections.Generic;
using Robocode.TankRoyale.BotApi;
using Robocode.TankRoyale.BotApi.Graphics;
using Robocode.TankRoyale.BotApi.Events;

namespace PathBot;

public class PathBot : Bot
{
    private List<(double x, double y)> Path { get; } = new();
    private int CurrentIndex { get; set; }

    static void Main(string[] args) => new PathBot().Start();

    public override void Run()
    {
        BodyColor = Color.FromRgb(235, 120, 180);
        TurretColor = Color.FromRgb(210, 90, 150);
        RadarColor = Color.FromRgb(255, 160, 210);
        BulletColor = Color.FromRgb(255, 200, 230);
        ScanColor = Color.FromRgb(255, 220, 235);

        AdjustGunForBodyTurn = true;
        AdjustRadarForGunTurn = true;
        MaxSpeed = Constants.MaxSpeed;

        while (IsRunning)
        {
            if (Path.Count > 0)
            {
                DrivePath();
            }

            SetTurnRadarRight(45);
            Go();
        }
    }

    public override void OnGameStarted(GameStartedEvent e)
    {
        var path = BuildGoldenSpiralPath();
        Path.Clear();
        Path.AddRange(path);
    }

    private List<(double x, double y)> BuildSquarePath()
    {
        var path = new List<(double x, double y)>();
        var size = Math.Min(ArenaWidth, ArenaHeight) / 2.5;
        var half = size / 2;
        var centerX = ArenaWidth / 2.0;
        var centerY = ArenaHeight / 2.0;

        path.Add((centerX - half, centerY - half));
        path.Add((centerX + half, centerY - half));
        path.Add((centerX + half, centerY + half));
        path.Add((centerX - half, centerY + half));

        return path;
    }

    private List<(double x, double y)> BuildGoldenSpiralPath()
    {
        var path = new List<(double x, double y)>();
        const double goldenRatio = 1.618;

        var margin = Math.Min(ArenaWidth, ArenaHeight) * 0.12;
        var minX = margin;
        var minY = margin;
        var maxX = ArenaWidth - margin;
        var maxY = ArenaHeight - margin;

        var centerX = ArenaWidth / 2.0;
        var centerY = ArenaHeight / 2.0;

        // Start from outside near top-left moving clockwise inward
        double width = maxX - minX;
        double height = maxY - minY;

        while (width > 30 && height > 30)
        {
            path.Add((centerX - width / 2, centerY - height / 2));
            path.Add((centerX + width / 2, centerY - height / 2));
            path.Add((centerX + width / 2, centerY + height / 2));
            path.Add((centerX - width / 2, centerY + height / 2));

            // shrink dimensions by golden ratio for next loop
            width /= goldenRatio;
            height /= goldenRatio;
        }

        return path;
    }

    private List<(double x, double y)> BuildStarPath()
    {
        var path = new List<(double x, double y)>();

        var margin = Math.Min(ArenaWidth, ArenaHeight) * 0.1;
        var radiusOuter = Math.Min(ArenaWidth, ArenaHeight) / 2.0 - margin;
        var radiusInner = radiusOuter * 0.5;
        var centerX = ArenaWidth / 2.0;
        var centerY = ArenaHeight / 2.0;

        for (int i = 0; i < 5; i++)
        {
            var outerAngle = (Math.PI * 2 / 5) * i - Math.PI / 2;
            var innerAngle = outerAngle + Math.PI / 5;

            var ox = centerX + radiusOuter * Math.Cos(outerAngle);
            var oy = centerY + radiusOuter * Math.Sin(outerAngle);
            var ix = centerX + radiusInner * Math.Cos(innerAngle);
            var iy = centerY + radiusInner * Math.Sin(innerAngle);

            path.Add((ox, oy));
            path.Add((ix, iy));
        }

        return path;
    }

    private void DrivePath()
    {
        var (targetX, targetY) = Path[CurrentIndex];
        var distance = DistanceTo(targetX, targetY);
        var targetDirection = DirectionTo(targetX, targetY);
        var turn = NormalizeRelativeAngle(targetDirection - Direction);

        SetTurnLeft(turn);

        var absTurn = Math.Abs(turn);
        double maxSpeed = absTurn > 80 ? 2.0 : absTurn > 45 ? 5.5 : Constants.MaxSpeed;

        if (distance < 80) maxSpeed = Math.Min(maxSpeed, 5.0);
        if (distance < 40) maxSpeed = Math.Min(maxSpeed, 3.0);

        MaxSpeed = maxSpeed;
        SetForward(distance);

        if (distance < 25)
        {
            CurrentIndex = (CurrentIndex + 1) % Path.Count;
        }
    }

    public override void OnTick(TickEvent e)
    {
        DrawPath();
    }

    public override void OnScannedBot(ScannedBotEvent e)
    {
        var gunBearing = GunBearingTo(e.X, e.Y);
        SetTurnGunLeft(gunBearing);

        var radarBearing = RadarBearingTo(e.X, e.Y);
        var radarOvershoot = Math.Sign(radarBearing) == 0 ? 1 : Math.Sign(radarBearing);
        SetTurnRadarLeft(radarBearing + radarOvershoot * 2);

        if (Math.Abs(gunBearing) <= 3 && GunHeat == 0)
        {
            var distance = DistanceTo(e.X, e.Y);
            var firePower = distance < 200 ? 3 : distance < 500 ? 2 : 1.2;
            Fire(Math.Min(firePower, Energy - 0.1));
        }

        if (gunBearing == 0)
        {
            Rescan();
        }
    }

    public override void OnHitBot(HitBotEvent e)
    {
        Fire(2.5);
        if (e.IsRammed)
        {
            SetTurnRight(15);
        }
    }

    private void DrawPath()
    {
        if (Path.Count == 0) return;

        Graphics.SetStrokeColor(Color.FromRgb(255, 200, 80));
        Graphics.SetStrokeWidth(2);
        for (int i = 0; i < Path.Count; i++)
        {
            var (x1, y1) = Path[i];
            var (x2, y2) = Path[(i + 1) % Path.Count];
            Graphics.DrawLine(x1, y1, x2, y2);
        }

        Graphics.SetStrokeColor(Color.FromRgb(255, 255, 180));
        Graphics.SetStrokeWidth(1);
        Graphics.SetFillColor(Color.FromRgb(255, 240, 180));
        for (int i = 0; i < Path.Count; i++)
        {
            var (x, y) = Path[i];
            if (i == CurrentIndex)
            {
                Graphics.SetFillColor(Color.FromRgb(255, 120, 120));
                Graphics.SetStrokeColor(Color.FromRgb(255, 80, 80));
                Graphics.FillCircle(x, y, 6);
                Graphics.DrawCircle(x, y, 6);
                Graphics.SetFillColor(Color.FromRgb(255, 240, 180));
                Graphics.SetStrokeColor(Color.FromRgb(255, 255, 180));
            }
            else
            {
                Graphics.FillCircle(x, y, 4);
                Graphics.DrawCircle(x, y, 4);
            }
        }
    }
}
