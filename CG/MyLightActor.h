// Fill out your copyright notice in the Description page of Project Settings.

#pragma once

#include "CoreMinimal.h"
#include "GameFramework/Actor.h"
#include "MyLightActor.generated.h"

UCLASS()
class MYPROJECT_API AMyLightActor : public AActor
{
	GENERATED_BODY()
	
public:	
	// Sets default values for this actor's properties
	AMyLightActor();

	virtual void OnConstruction(const FTransform& Transform) override;

protected:
	// Called when the game starts or when spawned
	virtual void BeginPlay() override;

public:	
	// Called every frame
	virtual void Tick(float DeltaTime) override;

private:
	UPROPERTY(VisibleAnywhere)
	class USceneComponent* RootScene;

	UPROPERTY(VisibleAnywhere)
	class UPointLightComponent* PointLight;

	UPROPERTY(VisibleAnywhere)
	class USpotLightComponent* SpotLight;

	UPROPERTY(EditAnywhere, Category = "Phong")
	class UMaterialParameterCollection* PhongMPC;

	UPROPERTY(EditAnywhere, Category = "Phong")
	float PhongLightIntensity;

	UPROPERTY(EditAnywhere, Category = "Phong")
	float PhongLightRadius;

	UPROPERTY(EditAnywhere, Category = "Phong")
	float Shininess;

	void UpdateMPC();

};