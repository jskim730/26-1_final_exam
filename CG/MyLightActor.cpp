// Fill out your copyright notice in the Description page of Project Settings.


#include "MyLightActor.h"
#include "Components/SceneComponent.h"
#include "Components/PointLightComponent.h"
#include "Components/SpotLightComponent.h"
#include "Kismet/KismetMaterialLibrary.h"
#include "Materials/MaterialParameterCollection.h"

// Sets default values
AMyLightActor::AMyLightActor()
{
	// Set this actor to call Tick() every frame.
	PrimaryActorTick.bCanEverTick = true;

	// Create Root Component
	RootScene = CreateDefaultSubobject<USceneComponent>(TEXT("RootScene"));
	RootComponent = RootScene;

	// Create Point Light Component
	PointLight = CreateDefaultSubobject<UPointLightComponent>(TEXT("PointLight"));
	PointLight->SetupAttachment(RootComponent);

	// Create Spot Light Component
	SpotLight = CreateDefaultSubobject<USpotLightComponent>(TEXT("SpotLight"));
	SpotLight->SetupAttachment(RootComponent);

	// Default Point Light Settings
	PointLight->SetLightColor(FLinearColor::Green);
	PointLight->SetIntensity(3000.0f);
	PointLight->SetAttenuationRadius(500.0f);

	// Default Spot Light Settings
	SpotLight->SetLightColor(FLinearColor::Red);
	SpotLight->SetIntensity(3000.0f);
	SpotLight->SetAttenuationRadius(500.0f);
	SpotLight->SetInnerConeAngle(15.0f);
	SpotLight->SetOuterConeAngle(35.0f);

	// Phong MPC Default Values
	PhongLightIntensity = 5.0f;
	PhongLightRadius = 1000.0f;
	Shininess = 32.0f;
}

// Called when the game starts or when spawned
void AMyLightActor::BeginPlay()
{
	Super::BeginPlay();

	UpdateMPC();
}

// Called every frame
void AMyLightActor::Tick(float DeltaTime)
{
	Super::Tick(DeltaTime);

	UpdateMPC();
}

void AMyLightActor::OnConstruction(const FTransform& Transform)
{
	Super::OnConstruction(Transform);

	UpdateMPC();
}

void AMyLightActor::UpdateMPC()
{
	if (!PhongMPC)
	{
		return;
	}

	FVector LightPos = GetActorLocation();

	UKismetMaterialLibrary::SetVectorParameterValue(
		GetWorld(),
		PhongMPC,
		TEXT("LightPosition"),
		FLinearColor(LightPos.X, LightPos.Y, LightPos.Z, 1.0f)
	);

	UKismetMaterialLibrary::SetVectorParameterValue(
		GetWorld(),
		PhongMPC,
		TEXT("LightColor"),
		FLinearColor::Red
	);

	UKismetMaterialLibrary::SetScalarParameterValue(
		GetWorld(),
		PhongMPC,
		TEXT("LightIntensity"),
		PhongLightIntensity
	);

	UKismetMaterialLibrary::SetScalarParameterValue(
		GetWorld(),
		PhongMPC,
		TEXT("LightRadius"),
		PhongLightRadius
	);

	UKismetMaterialLibrary::SetScalarParameterValue(
		GetWorld(),
		PhongMPC,
		TEXT("Shininess"),
		Shininess
	);
}
