import * as esbuild from 'esbuild';

const shared = {
  entryPoints: ['src/index.ts'],
  bundle: true,
  external: ['react', 'react-dom', 'react/jsx-runtime'],
  jsx: 'automatic',
  jsxImportSource: 'react',
};

await esbuild.build({ ...shared, format: 'esm', outfile: 'dist/index.es.js' });
await esbuild.build({ ...shared, format: 'cjs', outfile: 'dist/index.cjs.js' });

console.log('JS build complete.');
