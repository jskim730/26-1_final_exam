float3 normal = normalize(N);

float3 lightVector = LightPosition.xyz - WorldPos;
float distanceToLight = length(lightVector);
float3 lightDir = lightVector / max(distanceToLight, 0.0001);

float3 viewDir = normalize(CameraPos - WorldPos);
float3 halfVector = lightDir + viewDir;
float3 halfDir = halfVector / max(length(halfVector), 0.0001);

float ndotl = saturate(dot(normal, lightDir));
float ndoth = saturate(dot(normal, halfDir));

float radius = max(LightRadius, 1.0);
float attenuation = saturate(1.0 - distanceToLight / radius);
attenuation *= attenuation;

float intensity = max(LightIntensity, 0.0);
float shininessValue = max(Shininess, 1.0);

float ambientStrength = 0.03;
float diffuseStrength = 0.18;
float specularStrength = 0.55;

float3 ambient = ambientStrength * Albedo;
float3 diffuse = diffuseStrength * Albedo * LightColor.rgb * ndotl;
float3 specular = specularStrength * SpecColor * LightColor.rgb * pow(ndoth, shininessValue);

float3 color = ambient + attenuation * intensity * (diffuse + specular);

return color;
