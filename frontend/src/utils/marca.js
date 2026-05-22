/** Marca Cloudive no Termo Online (kit em cloudive/termo-online). */

export const marcaCloudiveAtiva = () =>
  import.meta.env.VITE_MARCA_CLOUDIVE !== "false";
