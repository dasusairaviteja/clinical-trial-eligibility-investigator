targetScope = 'resourceGroup'

@allowed(['ENG', 'TEST', 'PROD'])
param environment string
param location string = resourceGroup().location
param subnetId string
param managementCidr string
param sshPublicKey string
param vmSize string = 'Standard_B2s'
param imageVersion string

var prefix = 'triallens-${toLower(environment)}'
resource nsg 'Microsoft.Network/networkSecurityGroups@2024-05-01' = {
  name: '${prefix}-nsg'
  location: location
  properties: {
    securityRules: [
      {
        name: 'management-ssh'
        properties: {
          priority: 100
          direction: 'Inbound'
          access: 'Allow'
          protocol: 'Tcp'
          sourcePortRange: '*'
          destinationPortRange: '22'
          sourceAddressPrefix: managementCidr
          destinationAddressPrefix: '*'
        }
      }
      {
        name: 'deny-inbound'
        properties: {
          priority: 200
          direction: 'Inbound'
          access: 'Deny'
          protocol: '*'
          sourcePortRange: '*'
          destinationPortRange: '*'
          sourceAddressPrefix: '*'
          destinationAddressPrefix: '*'
        }
      }
    ]
  }
}
resource nic 'Microsoft.Network/networkInterfaces@2024-05-01' = {
  name: '${prefix}-nic'
  location: location
  properties: {
    networkSecurityGroup: { id: nsg.id }
    ipConfigurations: [{
      name: 'private'
      properties: {
        privateIPAllocationMethod: 'Dynamic'
        subnet: { id: subnetId }
      }
    }]
  }
}
resource vm 'Microsoft.Compute/virtualMachines@2024-11-01' = {
  name: prefix
  location: location
  tags: {
    environment: environment
    project: 'clinical-trial-investigator'
  }
  identity: { type: 'SystemAssigned' }
  properties: {
    hardwareProfile: { vmSize: vmSize }
    securityProfile: {
      securityType: 'TrustedLaunch'
      uefiSettings: {
        secureBootEnabled: true
        vTpmEnabled: true
      }
    }
    osProfile: {
      computerName: prefix
      adminUsername: 'trialadmin'
      linuxConfiguration: {
        disablePasswordAuthentication: true
        ssh: { publicKeys: [{
          path: '/home/trialadmin/.ssh/authorized_keys'
          keyData: sshPublicKey
        }] }
      }
    }
    storageProfile: {
      imageReference: {
        publisher: 'Canonical'
        offer: 'ubuntu-24_04-lts'
        sku: 'server'
        version: imageVersion
      }
      osDisk: {
        createOption: 'FromImage'
        deleteOption: 'Detach'
        managedDisk: { storageAccountType: 'StandardSSD_LRS' }
      }
    }
    networkProfile: { networkInterfaces: [{ id: nic.id }] }
  }
}
output vmResourceId string = vm.id
output managedIdentity string = vm.identity.principalId
